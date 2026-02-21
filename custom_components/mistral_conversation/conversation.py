"""Conversation platform for Mistral AI."""
from __future__ import annotations

import json
import logging
import re
from typing import Literal

import aiohttp
from homeassistant.components.conversation import (
    ConversationEntity,
    ConversationEntityFeature,
    ConversationInput,
    ConversationResult,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_KEY, MATCH_ALL
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError, TemplateError
from homeassistant.helpers import intent, template
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CONF_CONTROL_HA,
    CONF_MAX_TOKENS,
    CONF_MODEL,
    CONF_PROMPT,
    CONF_TEMPERATURE,
    DEFAULT_CONTROL_HA,
    DEFAULT_MAX_TOKENS,
    DEFAULT_MODEL,
    DEFAULT_PROMPT,
    DEFAULT_TEMPERATURE,
    DOMAIN,
    MISTRAL_API_BASE,
)

_LOGGER = logging.getLogger(__name__)

_JSON_RE = re.compile(r"```(?:json)?\s*(\{.*?\})\s*```|(\{[^`]*?\})", re.DOTALL)

_SIMPLE_SERVICES = {
    "homeassistant": ["turn_on", "turn_off", "toggle"],
    "light": ["turn_on", "turn_off", "toggle"],
    "switch": ["turn_on", "turn_off", "toggle"],
    "cover": ["open_cover", "close_cover", "stop_cover"],
    "media_player": ["turn_on", "turn_off", "toggle", "media_play", "media_pause",
                     "media_stop", "volume_up", "volume_down"],
    "fan": ["turn_on", "turn_off", "toggle"],
    "climate": ["turn_on", "turn_off"],
    "lock": ["lock", "unlock"],
    "alarm_control_panel": ["alarm_arm_away", "alarm_arm_home", "alarm_disarm"],
    "scene": ["turn_on"],
    "script": ["turn_on"],
    "automation": ["turn_on", "turn_off", "trigger"],
}


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up conversation entities."""
    async_add_entities([MistralConversationEntity(hass, config_entry)])


def _get_exposed_entities(hass: HomeAssistant) -> list:
    """Return exposed entity states."""
    try:
        from homeassistant.components.homeassistant.exposed_entities import (
            async_should_expose,
        )
        from homeassistant.components import conversation as _conv
        return [
            s for s in hass.states.async_all()
            if async_should_expose(hass, _conv.DOMAIN, s.entity_id)
        ]
    except Exception:
        return list(hass.states.async_all())


def _build_entity_context(hass: HomeAssistant) -> str:
    """Build compact entity list for system prompt."""
    states = _get_exposed_entities(hass)
    if not states:
        return ""
    lines = ["Exposed smart home devices:"]
    for s in states:
        name = s.attributes.get("friendly_name", s.entity_id)
        lines.append(f"  {s.entity_id} | {name} | state: {s.state}")
    return "\n".join(lines)


def _extract_json(text: str) -> dict | None:
    """Extract first JSON object from text, handling markdown fences."""
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        pass
    for match in _JSON_RE.finditer(text):
        candidate = match.group(1) or match.group(2)
        if candidate:
            try:
                return json.loads(candidate.strip())
            except json.JSONDecodeError:
                continue
    return None


class MistralConversationEntity(ConversationEntity):
    """Mistral AI conversation agent entity."""

    _attr_has_entity_name = True
    _attr_name = None
    _attr_supported_features = ConversationEntityFeature.CONTROL

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize."""
        self.hass = hass
        self._entry = entry
        self._attr_unique_id = entry.entry_id
        self._history: dict[str, list[dict]] = {}

    @property
    def supported_languages(self) -> list[str] | Literal["*"]:
        return MATCH_ALL

    @property
    def device_info(self):
        from homeassistant.helpers.device_registry import DeviceInfo
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry.entry_id)},
            name="Mistral AI",
            manufacturer="Mistral AI",
            model=self._entry.options.get(CONF_MODEL, DEFAULT_MODEL),
        )

    async def _async_handle_message(self, user_input: ConversationInput, chat_log=None) -> ConversationResult:
        return await self._process(user_input)

    async def async_process(self, user_input: ConversationInput) -> ConversationResult:
        return await self._process(user_input)

    async def _process(self, user_input: ConversationInput) -> ConversationResult:
        opts = self._entry.options
        api_key = self._entry.data[CONF_API_KEY]
        model = opts.get(CONF_MODEL, DEFAULT_MODEL)
        max_tokens = int(opts.get(CONF_MAX_TOKENS, DEFAULT_MAX_TOKENS))
        temperature = float(opts.get(CONF_TEMPERATURE, DEFAULT_TEMPERATURE))
        control_ha = opts.get(CONF_CONTROL_HA, DEFAULT_CONTROL_HA)
        raw_prompt = opts.get(CONF_PROMPT, DEFAULT_PROMPT)

        try:
            system_prompt = template.Template(raw_prompt, self.hass).async_render(
                {"ha_name": self.hass.config.location_name},
                parse_result=False,
            )
        except TemplateError as err:
            _LOGGER.error("Error rendering prompt template: %s", err)
            system_prompt = raw_prompt

        if control_ha:
            entity_ctx = _build_entity_context(self.hass)
            if entity_ctx:
                system_prompt += f"\n\n{entity_ctx}"
            system_prompt += (
                "\n\nWhen the user wants to control a device, respond with ONLY a raw JSON "
                "object on one line, no extra text, no markdown:\n"
                '{"action":"call_service","domain":"DOMAIN","service":"SERVICE","entity_id":"ENTITY_ID"}\n'
                "Example: turn off kitchen light → "
                '{"action":"call_service","domain":"light","service":"turn_off","entity_id":"light.lamp_keuken"}\n'
                "For questions or information, reply normally in plain text."
            )

        conv_id = user_input.conversation_id or self._new_id()
        history = self._history.setdefault(conv_id, [])
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(history)
        messages.append({"role": "user", "content": user_input.text})

        # Mistral temperature is 0.0–1.0; clamp defensively to avoid 400 errors
        safe_temp = max(0.0, min(1.0, float(temperature)))
        # Do NOT send both temperature and top_p — Mistral returns 400 Bad Request
        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": int(max_tokens),
            "temperature": safe_temp,
        }
        _LOGGER.debug("Mistral payload: model=%s temperature=%s max_tokens=%s", model, safe_temp, max_tokens)

        session = async_get_clientsession(self.hass)
        try:
            async with session.post(
                f"{MISTRAL_API_BASE}/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=aiohttp.ClientTimeout(total=30),
            ) as resp:
                if resp.status == 401:
                    raise HomeAssistantError("Invalid Mistral AI API key")
                if resp.status == 429:
                    raise HomeAssistantError("Mistral AI rate limit exceeded")
                resp.raise_for_status()
                data = await resp.json()
        except aiohttp.ClientError as err:
            _LOGGER.error("Mistral AI API error: %s", err)
            intent_response = intent.IntentResponse(language=user_input.language)
            intent_response.async_set_error(
                intent.IntentResponseErrorCode.UNKNOWN,
                f"Sorry, kon Mistral AI niet bereiken: {err}",
            )
            return ConversationResult(response=intent_response, conversation_id=conv_id)

        raw_reply = data["choices"][0]["message"]["content"].strip()
        reply = raw_reply

        if control_ha:
            action = _extract_json(raw_reply)
            if action and action.get("action") == "call_service":
                domain = action.get("domain", "")
                service = action.get("service", "")
                entity_id = action.get("entity_id", "")
                _LOGGER.debug("Executing service: %s.%s on %s", domain, service, entity_id)
                try:
                    await self.hass.services.async_call(
                        domain,
                        service,
                        {"entity_id": entity_id},
                        blocking=True,
                        context=user_input.context,
                    )
                    state = self.hass.states.get(entity_id)
                    friendly = (
                        state.attributes.get("friendly_name", entity_id)
                        if state else entity_id
                    )
                    verb = (
                        service.replace("turn_on", "aangezet")
                               .replace("turn_off", "uitgezet")
                               .replace("toggle", "omgeschakeld")
                               .replace("open_cover", "geopend")
                               .replace("close_cover", "gesloten")
                               .replace("lock", "vergrendeld")
                               .replace("unlock", "ontgrendeld")
                               .replace("_", " ")
                    )
                    reply = f"Klaar! {friendly} is {verb}."
                except HomeAssistantError as err:
                    _LOGGER.error("Service call failed: %s", err)
                    reply = f"Sorry, dat is mislukt: {err}"
                except Exception as err:
                    _LOGGER.exception("Unexpected error in service call")
                    reply = "Sorry, er ging iets onverwachts mis."

        history.append({"role": "user", "content": user_input.text})
        history.append({"role": "assistant", "content": raw_reply})
        if len(history) > 40:
            self._history[conv_id] = history[-40:]

        intent_response = intent.IntentResponse(language=user_input.language)
        intent_response.async_set_speech(reply)
        return ConversationResult(response=intent_response, conversation_id=conv_id)

    @staticmethod
    def _new_id() -> str:
        from homeassistant.util import ulid
        return ulid.ulid_now()
