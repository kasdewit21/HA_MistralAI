"""Conversation platform for Mistral AI — supports model mode and agent mode."""
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
    CONF_AGENT_ID,
    CONF_CONTROL_HA,
    CONF_MAX_TOKENS,
    CONF_MODE,
    CONF_MODEL,
    CONF_PROMPT,
    CONF_TEMPERATURE,
    DEFAULT_CONTROL_HA,
    DEFAULT_MAX_TOKENS,
    DEFAULT_MODE,
    DEFAULT_MODEL,
    DEFAULT_PROMPT,
    DEFAULT_TEMPERATURE,
    DOMAIN,
    MISTRAL_API_BASE,
    MODE_AGENT,
    MODE_MODEL,
)

_LOGGER = logging.getLogger(__name__)

_JSON_RE = re.compile(r"```(?:json)?\s*(\{.*?\})\s*```|(\{[^`]*?\})", re.DOTALL)

_ALLOWED_SERVICES: dict[str, list[str]] = {
    "homeassistant": ["turn_on", "turn_off", "toggle"],
    "light":         ["turn_on", "turn_off", "toggle"],
    "switch":        ["turn_on", "turn_off", "toggle"],
    "cover":         ["open_cover", "close_cover", "stop_cover"],
    "media_player":  ["turn_on", "turn_off", "toggle", "media_play", "media_pause",
                      "media_stop", "volume_up", "volume_down"],
    "fan":           ["turn_on", "turn_off", "toggle"],
    "climate":       ["turn_on", "turn_off"],
    "lock":          ["lock", "unlock"],
    "alarm_control_panel": ["alarm_arm_away", "alarm_arm_home", "alarm_disarm"],
    "scene":         ["turn_on"],
    "script":        ["turn_on"],
    "automation":    ["turn_on", "turn_off", "trigger"],
}

# Per-service past-tense verbs, keyed by language code
_SERVICE_VERBS: dict[str, dict[str, str]] = {
    "turn_on":    {"nl": "aangezet",     "en": "turned on",      "de": "eingeschaltet",   "fr": "allumé",         "es": "encendido"},
    "turn_off":   {"nl": "uitgezet",     "en": "turned off",     "de": "ausgeschaltet",   "fr": "éteint",         "es": "apagado"},
    "toggle":     {"nl": "omgeschakeld", "en": "toggled",        "de": "umgeschaltet",    "fr": "basculé",        "es": "alternado"},
    "open_cover": {"nl": "geopend",      "en": "opened",         "de": "geöffnet",        "fr": "ouvert",         "es": "abierto"},
    "close_cover":{"nl": "gesloten",     "en": "closed",         "de": "geschlossen",     "fr": "fermé",          "es": "cerrado"},
    "stop_cover": {"nl": "gestopt",      "en": "stopped",        "de": "gestoppt",        "fr": "arrêté",         "es": "detenido"},
    "lock":       {"nl": "vergrendeld",  "en": "locked",         "de": "verriegelt",      "fr": "verrouillé",     "es": "bloqueado"},
    "unlock":     {"nl": "ontgrendeld",  "en": "unlocked",       "de": "entriegelt",      "fr": "déverrouillé",   "es": "desbloqueado"},
    "media_play": {"nl": "gestart",      "en": "started",        "de": "gestartet",       "fr": "démarré",        "es": "iniciado"},
    "media_pause":{"nl": "gepauzeerd",   "en": "paused",         "de": "pausiert",        "fr": "mis en pause",   "es": "pausado"},
    "media_stop": {"nl": "gestopt",      "en": "stopped",        "de": "gestoppt",        "fr": "arrêté",         "es": "detenido"},
    "volume_up":  {"nl": "harder gezet", "en": "turned up",      "de": "lauter gestellt", "fr": "monté",          "es": "subido"},
    "volume_down":{"nl": "zachter gezet","en": "turned down",    "de": "leiser gestellt", "fr": "baissé",         "es": "bajado"},
}

# UI strings per language code (falls back to "en")
_STRINGS: dict[str, dict[str, str]] = {
    "done": {
        "nl": "Klaar", "en": "Done", "de": "Erledigt", "fr": "Fait", "es": "Listo",
    },
    "is": {
        "nl": "is", "en": "is", "de": "ist", "fr": "est", "es": "está",
    },
    "blocked": {
        "nl": "Ik kan die actie niet uitvoeren ({domain}.{service} is niet toegestaan).",
        "en": "I cannot perform that action ({domain}.{service} is not allowed).",
        "de": "Ich kann diese Aktion nicht ausführen ({domain}.{service} ist nicht erlaubt).",
        "fr": "Je ne peux pas effectuer cette action ({domain}.{service} n'est pas autorisé).",
        "es": "No puedo realizar esa acción ({domain}.{service} no está permitido).",
    },
    "failed": {
        "nl": "Sorry, dat is mislukt: {err}",
        "en": "Sorry, that failed: {err}",
        "de": "Entschuldigung, das hat nicht geklappt: {err}",
        "fr": "Désolé, ça a échoué : {err}",
        "es": "Lo siento, eso falló: {err}",
    },
    "unexpected": {
        "nl": "Sorry, er ging iets onverwachts mis.",
        "en": "Sorry, something unexpected went wrong.",
        "de": "Entschuldigung, es ist ein unerwarteter Fehler aufgetreten.",
        "fr": "Désolé, une erreur inattendue s'est produite.",
        "es": "Lo siento, algo inesperado salió mal.",
    },
    "api_error": {
        "nl": "Sorry, kon Mistral AI niet bereiken: {err}",
        "en": "Sorry, could not reach Mistral AI: {err}",
        "de": "Entschuldigung, Mistral AI war nicht erreichbar: {err}",
        "fr": "Désolé, impossible de contacter Mistral AI : {err}",
        "es": "Lo siento, no se pudo conectar a Mistral AI: {err}",
    },
    "no_agent_id": {
        "nl": "Fout: geen Agent ID ingesteld. Vul een Agent ID in via de integratie-opties.",
        "en": "Error: no Agent ID configured. Please set an Agent ID in the integration options.",
        "de": "Fehler: Keine Agent-ID konfiguriert. Bitte legen Sie eine Agent-ID in den Integrationsoptionen fest.",
        "fr": "Erreur : aucun identifiant d'agent configuré. Veuillez en définir un dans les options d'intégration.",
        "es": "Error: no hay ID de agente configurado. Por favor, configure uno en las opciones de integración.",
    },
}


def _lang_code(language: str) -> str:
    """Normalise 'de-DE' → 'de', already-short codes pass through."""
    return language.split("-")[0].lower() if language else "en"


def _t(key: str, language: str, **kwargs) -> str:
    """Return a translated string, falling back to English."""
    lang = _lang_code(language)
    strings = _STRINGS.get(key, {})
    text = strings.get(lang) or strings.get("en", key)
    return text.format(**kwargs) if kwargs else text


def _service_verb(service: str, language: str) -> str:
    """Return a localised past-tense verb for the service action."""
    lang = _lang_code(language)
    verbs = _SERVICE_VERBS.get(service, {})
    return verbs.get(lang) or verbs.get("en") or service.replace("_", " ")


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up conversation entity."""
    async_add_entities([MistralConversationEntity(hass, config_entry)])


def _get_exposed_entities(hass: HomeAssistant) -> list:
    try:
        from homeassistant.components.homeassistant.exposed_entities import async_should_expose
        from homeassistant.components import conversation as _conv
        return [s for s in hass.states.async_all()
                if async_should_expose(hass, _conv.DOMAIN, s.entity_id)]
    except Exception:
        return list(hass.states.async_all())


def _build_entity_context(hass: HomeAssistant) -> str:
    states = _get_exposed_entities(hass)
    if not states:
        return ""
    lines = ["Exposed smart home devices:"]
    for s in states:
        name = s.attributes.get("friendly_name", s.entity_id)
        lines.append(f"  {s.entity_id} | {name} | state: {s.state}")
    return "\n".join(lines)


def _extract_json(text: str) -> dict | None:
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
    """Mistral AI conversation agent — model mode or agent mode."""

    _attr_has_entity_name = True
    _attr_name = None
    _attr_supported_features = ConversationEntityFeature.CONTROL

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self._entry = entry
        # Use _conversation suffix so this device is separate from the STT device
        self._attr_unique_id = f"{entry.entry_id}_conversation"
        self._history: dict[str, list[dict]] = {}

    @property
    def supported_languages(self) -> list[str] | Literal["*"]:
        return MATCH_ALL

    @property
    def device_info(self) -> DeviceInfo:
        """Own device for the conversation agent, separate from STT."""
        opts = self._entry.options
        mode = opts.get(CONF_MODE, DEFAULT_MODE)
        if mode == MODE_AGENT:
            model_label = f"Agent: {opts.get(CONF_AGENT_ID, 'unknown')}"
        else:
            model_label = opts.get(CONF_MODEL, DEFAULT_MODEL)

        return DeviceInfo(
            # Unique identifiers → creates a SEPARATE device from STT
            identifiers={(DOMAIN, f"{self._entry.entry_id}_conversation")},
            name="Mistral AI Conversation",
            manufacturer="Mistral AI",
            model=model_label,
            entry_type=DeviceEntryType.SERVICE,
            configuration_url="https://console.mistral.ai",
        )

    async def _async_handle_message(self, user_input: ConversationInput, chat_log=None) -> ConversationResult:
        return await self._process(user_input)

    async def async_process(self, user_input: ConversationInput) -> ConversationResult:
        return await self._process(user_input)

    async def _process(self, user_input: ConversationInput) -> ConversationResult:
        opts = self._entry.options
        api_key = self._entry.data[CONF_API_KEY]
        mode = opts.get(CONF_MODE, DEFAULT_MODE)
        control_ha = opts.get(CONF_CONTROL_HA, DEFAULT_CONTROL_HA)
        conv_id = user_input.conversation_id or self._new_id()
        language = user_input.language or "en"

        if mode == MODE_AGENT:
            result = await self._call_agent(
                api_key=api_key,
                agent_id=opts.get(CONF_AGENT_ID, ""),
                user_text=user_input.text,
                conv_id=conv_id,
                language=language,
            )
        else:
            result = await self._call_model(
                api_key=api_key,
                opts=opts,
                user_text=user_input.text,
                conv_id=conv_id,
                control_ha=control_ha,
                language=language,
            )

        if isinstance(result, ConversationResult):
            return result

        raw_reply = result
        reply = await self._maybe_execute_service(raw_reply, user_input, control_ha, language)

        history = self._history.setdefault(conv_id, [])
        history.append({"role": "user", "content": user_input.text})
        history.append({"role": "assistant", "content": raw_reply})
        if len(history) > 40:
            self._history[conv_id] = history[-40:]

        intent_response = intent.IntentResponse(language=language)
        intent_response.async_set_speech(reply)
        return ConversationResult(response=intent_response, conversation_id=conv_id)

    async def _call_model(
        self, api_key: str, opts: dict, user_text: str, conv_id: str,
        control_ha: bool, language: str = "en"
    ) -> str | ConversationResult:
        model = opts.get(CONF_MODEL, DEFAULT_MODEL)
        max_tokens = int(opts.get(CONF_MAX_TOKENS, DEFAULT_MAX_TOKENS))
        temperature = max(0.0, min(1.0, float(opts.get(CONF_TEMPERATURE, DEFAULT_TEMPERATURE))))
        raw_prompt = opts.get(CONF_PROMPT, DEFAULT_PROMPT)

        try:
            system_prompt = template.Template(raw_prompt, self.hass).async_render(
                {"ha_name": self.hass.config.location_name}, parse_result=False
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
                "object on one line, no extra text, no markdown:\n"
                '{"action":"call_service","domain":"DOMAIN","service":"SERVICE","entity_id":"ENTITY_ID"}\n'
                "For questions or information, reply normally in plain text."
            )

        history = self._history.get(conv_id, [])
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(history)
        messages.append({"role": "user", "content": user_text})

        return await self._post_chat(
            api_key=api_key,
            endpoint=f"{MISTRAL_API_BASE}/chat/completions",
            payload={
                "model": model,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
            },
            conv_id=conv_id,
            language=language,
        )

    async def _call_agent(
        self, api_key: str, agent_id: str, user_text: str, conv_id: str, language: str = "en"
    ) -> str | ConversationResult:
        if not agent_id:
            return _t("no_agent_id", language)

        history = self._history.get(conv_id, [])
        messages = list(history)
        messages.append({"role": "user", "content": user_text})

        return await self._post_chat(
            api_key=api_key,
            endpoint=f"{MISTRAL_API_BASE}/agents/completions",
            payload={"agent_id": agent_id, "messages": messages},
            conv_id=conv_id,
            language=language,
        )

    async def _post_chat(
        self, api_key: str, endpoint: str, payload: dict, conv_id: str, language: str = "en"
    ) -> str | ConversationResult:
        session = async_get_clientsession(self.hass)
        try:
            async with session.post(
                endpoint,
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json=payload,
                timeout=aiohttp.ClientTimeout(total=30),
            ) as resp:
                if resp.status == 401:
                    raise HomeAssistantError("Invalid Mistral AI API key")
                if resp.status == 429:
                    raise HomeAssistantError("Mistral AI rate limit exceeded")
                if resp.status >= 400:
                    body = await resp.text()
                    _LOGGER.error("Mistral API HTTP %s. Keys=%s Body=%s",
                                  resp.status, list(payload.keys()), body)
                    raise HomeAssistantError(f"Mistral API error {resp.status}: {body}")
                data = await resp.json()
        except (aiohttp.ClientError, HomeAssistantError) as err:
            _LOGGER.error("Mistral AI API error: %s", err)
            intent_response = intent.IntentResponse(language=language)
            intent_response.async_set_error(
                intent.IntentResponseErrorCode.UNKNOWN,
                _t("api_error", language, err=err),
            )
            return ConversationResult(response=intent_response, conversation_id=conv_id)

        return data["choices"][0]["message"]["content"].strip()

    async def _maybe_execute_service(
        self, raw_reply: str, user_input: ConversationInput, control_ha: bool, language: str = "en"
    ) -> str:
        if not control_ha:
            return raw_reply

        action = _extract_json(raw_reply)
        if not (action and action.get("action") == "call_service"):
            return raw_reply

        domain  = action.get("domain", "")
        service = action.get("service", "")
        entity_id = action.get("entity_id", "")

        if service not in _ALLOWED_SERVICES.get(domain, []) and domain != "homeassistant":
            _LOGGER.warning("Blocked service call %s.%s", domain, service)
            return _t("blocked", language, domain=domain, service=service)

        try:
            await self.hass.services.async_call(
                domain, service, {"entity_id": entity_id},
                blocking=True, context=user_input.context,
            )
            state = self.hass.states.get(entity_id)
            friendly = state.attributes.get("friendly_name", entity_id) if state else entity_id
            verb = _service_verb(service, language)
            done = _t("done", language)
            is_word = _t("is", language)
            return f"{done}! {friendly} {is_word} {verb}."
        except HomeAssistantError as err:
            _LOGGER.error("Service call failed: %s", err)
            return _t("failed", language, err=err)
        except Exception:
            _LOGGER.exception("Unexpected error in service call")
            return _t("unexpected", language)

    @staticmethod
    def _new_id() -> str:
        from homeassistant.util import ulid
        return ulid.ulid_now()
