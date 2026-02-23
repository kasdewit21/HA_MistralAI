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
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CONF_CONTINUE_CONVERSATION,
    CONF_CONTROL_HA,
    CONF_MAX_TOKENS,
    CONF_MODEL,
    CONF_PROMPT,
    CONF_TEMPERATURE,
    DEFAULT_CONTINUE_CONVERSATION,
    DEFAULT_CONTROL_HA,
    DEFAULT_MAX_TOKENS,
    DEFAULT_MODEL,
    DEFAULT_PROMPT,
    DEFAULT_TEMPERATURE,
    DOMAIN,
    MISTRAL_API_BASE,
)

_LOGGER = logging.getLogger(__name__)

# Regex to extract a JSON object from model output, even inside markdown fences
_JSON_RE = re.compile(r"```(?:json)?\s*(\{.*?\})\s*```|(\{[^`]*?\})", re.DOTALL)

# ---------------------------------------------------------------------------
# Allowed HA service calls (safety allow-list)
# ---------------------------------------------------------------------------
_ALLOWED_SERVICES: dict[str, list[str]] = {
    "homeassistant": ["turn_on", "turn_off", "toggle"],
    "light":         ["turn_on", "turn_off", "toggle"],
    "switch":        ["turn_on", "turn_off", "toggle"],
    "cover":         ["open_cover", "close_cover", "stop_cover", "set_cover_position"],
    "media_player":  [
        "turn_on", "turn_off", "toggle",
        "media_play", "media_pause", "media_stop",
        "volume_up", "volume_down", "volume_set", "volume_mute",
        "select_source", "select_sound_mode",
        "media_next_track", "media_previous_track",
    ],
    "fan":           ["turn_on", "turn_off", "toggle", "set_percentage", "set_preset_mode"],
    "climate":       ["turn_on", "turn_off", "set_temperature", "set_hvac_mode"],
    "lock":          ["lock", "unlock"],
    "alarm_control_panel": ["alarm_arm_away", "alarm_arm_home", "alarm_disarm"],
    "scene":         ["turn_on"],
    "script":        ["turn_on"],
    "automation":    ["turn_on", "turn_off", "trigger"],
    "input_boolean": ["turn_on", "turn_off", "toggle"],
    "input_number":  ["set_value"],
    "number":        ["set_value"],
}


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Mistral AI conversation entity."""
    async_add_entities([MistralConversationEntity(hass, config_entry)])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_exposed_entities(hass: HomeAssistant) -> list:
    """Return all entity states that are exposed to voice assistants."""
    try:
        from homeassistant.components.homeassistant.exposed_entities import (
            async_should_expose,
        )
        from homeassistant.components import conversation as _conv

        return [
            s for s in hass.states.async_all()
            if async_should_expose(hass, _conv.DOMAIN, s.entity_id)
        ]
    except Exception:  # pylint: disable=broad-except
        return list(hass.states.async_all())


def _build_entity_context(hass: HomeAssistant) -> str:
    """Build a compact text list of exposed entities for the system prompt."""
    states = _get_exposed_entities(hass)
    if not states:
        return ""
    lines = ["Exposed smart home devices:"]
    for s in states:
        name = s.attributes.get("friendly_name", s.entity_id)
        lines.append(f"  {s.entity_id} | {name} | state: {s.state}")
    return "\n".join(lines)


def _extract_json(text: str) -> dict | None:
    """Extract the first JSON object from text, handling markdown fences."""
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


def _reply_contains_question(text: str) -> bool:
    """Return True if the reply ends with or contains a question."""
    return "?" in text


# ---------------------------------------------------------------------------
# Entity
# ---------------------------------------------------------------------------

class MistralConversationEntity(ConversationEntity):
    """Mistral AI conversation agent entity."""

    _attr_has_entity_name = True
    _attr_name = None
    _attr_supported_features = ConversationEntityFeature.CONTROL

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_conversation"
        self._history: dict[str, list[dict]] = {}

    @property
    def supported_languages(self) -> list[str] | Literal["*"]:
        return MATCH_ALL

    @property
    def device_info(self) -> DeviceInfo:
        """Separate device from STT entity."""
        model = self._entry.options.get(CONF_MODEL, DEFAULT_MODEL)
        return DeviceInfo(
            identifiers={(DOMAIN, f"{self._entry.entry_id}_conversation")},
            name="Mistral AI Conversation",
            manufacturer="Mistral AI",
            model=model,
            entry_type=DeviceEntryType.SERVICE,
            configuration_url="https://console.mistral.ai",
        )

    # ------------------------------------------------------------------
    # HA 2024.6+ API (preferred)
    # ------------------------------------------------------------------
    async def _async_handle_message(
        self,
        user_input: ConversationInput,
        chat_log=None,
    ) -> ConversationResult:
        return await self._process(user_input)

    # ------------------------------------------------------------------
    # Legacy API (< 2024.6)
    # ------------------------------------------------------------------
    async def async_process(self, user_input: ConversationInput) -> ConversationResult:
        return await self._process(user_input)

    # ------------------------------------------------------------------
    # Core processing
    # ------------------------------------------------------------------
    async def _process(self, user_input: ConversationInput) -> ConversationResult:
        opts = self._entry.options
        api_key = self._entry.data[CONF_API_KEY]
        control_ha = opts.get(CONF_CONTROL_HA, DEFAULT_CONTROL_HA)
        continue_conversation_enabled = opts.get(
            CONF_CONTINUE_CONVERSATION, DEFAULT_CONTINUE_CONVERSATION
        )
        conv_id = user_input.conversation_id or self._new_id()

        # --- Build system prompt ------------------------------------------
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
            ctx = _build_entity_context(self.hass)
            if ctx:
                system_prompt += f"\n\n{ctx}"
            system_prompt += (
                "\n\nWhen the user wants to control a device, respond with ONLY a raw JSON "
                "object on one line — no extra text, no markdown fences:\n"
                '{"action":"call_service","domain":"DOMAIN","service":"SERVICE","entity_id":"ENTITY_ID",'
                '"service_data":{},"confirmation":"A short friendly confirmation in the user\'s language"}\n'
                "Fill 'service_data' with any extra parameters needed (e.g. volume_level, temperature). "
                "Leave it as {} if no extra parameters are needed. "
                "Always write the 'confirmation' in the same language the user is speaking. "
                "For information requests or general conversation, reply normally in plain text."
            )

        # --- Build message history ----------------------------------------
        history = self._history.get(conv_id, [])
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(history)
        messages.append({"role": "user", "content": user_input.text})

        # --- Call Mistral API ---------------------------------------------
        model = opts.get(CONF_MODEL, DEFAULT_MODEL)
        max_tokens = int(opts.get(CONF_MAX_TOKENS, DEFAULT_MAX_TOKENS))
        temperature = max(0.0, min(1.0, float(opts.get(CONF_TEMPERATURE, DEFAULT_TEMPERATURE))))

        raw_reply = await self._post_chat(
            api_key=api_key,
            payload={
                "model": model,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
            },
            conv_id=conv_id,
            language=user_input.language,
        )

        # _post_chat returns a ConversationResult directly on error
        if isinstance(raw_reply, ConversationResult):
            return raw_reply

        # --- Optionally execute a HA service call -------------------------
        reply = await self._maybe_execute_service(raw_reply, user_input, control_ha)

        # --- Update rolling history (max 20 turns = 40 messages) ----------
        updated_history = list(history)
        updated_history.append({"role": "user", "content": user_input.text})
        updated_history.append({"role": "assistant", "content": raw_reply})
        self._history[conv_id] = updated_history[-40:]

        # --- Decide whether to keep the microphone open -------------------
        # If enabled, any reply ending with a question keeps listening.
        should_continue = (
            continue_conversation_enabled
            and _reply_contains_question(reply)
        )

        intent_response = intent.IntentResponse(language=user_input.language)
        intent_response.async_set_speech(reply)
        return ConversationResult(
            response=intent_response,
            conversation_id=conv_id,
            continue_conversation=should_continue,
        )

    # ------------------------------------------------------------------
    # HTTP call
    # ------------------------------------------------------------------
    async def _post_chat(
        self,
        api_key: str,
        payload: dict,
        conv_id: str,
        language: str,
    ) -> str | ConversationResult:
        """POST to the Mistral chat completions endpoint."""
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
                if resp.status >= 400:
                    body = await resp.text()
                    _LOGGER.error(
                        "Mistral API HTTP %s — model=%s body=%s",
                        resp.status,
                        payload.get("model"),
                        body,
                    )
                    raise HomeAssistantError(f"Mistral API error {resp.status}: {body}")
                data = await resp.json()

        except (aiohttp.ClientError, HomeAssistantError) as err:
            _LOGGER.error("Mistral AI request failed: %s", err)
            intent_response = intent.IntentResponse(language=language)
            intent_response.async_set_error(
                intent.IntentResponseErrorCode.UNKNOWN,
                f"Sorry, I could not reach Mistral AI: {err}",
            )
            return ConversationResult(response=intent_response, conversation_id=conv_id)

        return data["choices"][0]["message"]["content"].strip()

    # ------------------------------------------------------------------
    # HA service execution
    # ------------------------------------------------------------------
    async def _maybe_execute_service(
        self,
        raw_reply: str,
        user_input: ConversationInput,
        control_ha: bool,
    ) -> str:
        """If raw_reply is a JSON service call, execute it and return the AI-generated confirmation."""
        if not control_ha:
            return raw_reply

        action = _extract_json(raw_reply)
        if not (action and action.get("action") == "call_service"):
            return raw_reply

        domain      = action.get("domain", "")
        service     = action.get("service", "")
        entity_id   = action.get("entity_id", "")
        service_data = action.get("service_data") or {}
        # Confirmation is generated by the AI in the user's language
        confirmation = action.get("confirmation", "").strip()

        if service not in _ALLOWED_SERVICES.get(domain, []) and domain != "homeassistant":
            _LOGGER.warning("Blocked service call: %s.%s", domain, service)
            # Return the confirmation if present (AI may have written a refusal),
            # otherwise fall back to a neutral message.
            return confirmation or f"({domain}.{service} is not permitted)"

        # Merge entity_id into service_data
        call_data: dict = {"entity_id": entity_id, **service_data}

        try:
            await self.hass.services.async_call(
                domain,
                service,
                call_data,
                blocking=True,
                context=user_input.context,
            )
        except HomeAssistantError as err:
            _LOGGER.error("Service call %s.%s failed: %s", domain, service, err)
            return confirmation or str(err)
        except Exception:  # pylint: disable=broad-except
            _LOGGER.exception("Unexpected error executing service %s.%s", domain, service)
            return confirmation or "Something went wrong while executing that action."

        # Return the AI-generated confirmation (already in the user's language)
        return confirmation or entity_id

    @staticmethod
    def _new_id() -> str:
        from homeassistant.util import ulid
        return ulid.ulid_now()
