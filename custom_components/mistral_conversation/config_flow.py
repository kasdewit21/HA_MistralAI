"""Config flow for Mistral AI Conversation."""
from __future__ import annotations

import logging
from typing import Any

import aiohttp
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_API_KEY
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .stt import LANGUAGE_OPTIONS
from .const import (
    CHAT_MODELS,
    CONF_AGENT_ID,
    CONF_CONTROL_HA,
    CONF_MAX_TOKENS,
    CONF_MODE,
    CONF_MODEL,
    CONF_PROMPT,
    CONF_STT_LANGUAGE,
    CONF_TEMPERATURE,
    DEFAULT_CONTROL_HA,
    DEFAULT_MAX_TOKENS,
    DEFAULT_MODE,
    DEFAULT_MODEL,
    DEFAULT_PROMPT,
    DEFAULT_STT_LANGUAGE,
    DEFAULT_TEMPERATURE,
    DOMAIN,
    MISTRAL_API_BASE,
    MODE_AGENT,
    MODE_MODEL,
)

_LOGGER = logging.getLogger(__name__)


class MistralConversationConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Mistral AI Conversation."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            error = await self._test_api_key(user_input[CONF_API_KEY])
            if error:
                errors["base"] = error
            else:
                await self.async_set_unique_id(DOMAIN)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title="Mistral AI Conversation",
                    data={CONF_API_KEY: user_input[CONF_API_KEY]},
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_API_KEY): selector.TextSelector(
                    selector.TextSelectorConfig(type=selector.TextSelectorType.PASSWORD)
                ),
            }),
            errors=errors,
            description_placeholders={"api_key_url": "https://console.mistral.ai/api-keys"},
        )

    async def _test_api_key(self, api_key: str) -> str | None:
        session = async_get_clientsession(self.hass)
        try:
            async with session.get(
                f"{MISTRAL_API_BASE}/models",
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                if resp.status == 401:
                    return "invalid_auth"
                if resp.status != 200:
                    return "cannot_connect"
        except aiohttp.ClientConnectorError:
            return "cannot_connect"
        except Exception:
            _LOGGER.exception("Unexpected error testing API key")
            return "unknown"
        return None

    @staticmethod
    def async_get_options_flow(config_entry: config_entries.ConfigEntry) -> "MistralOptionsFlow":
        # NOTE: No __init__, no self.config_entry assignment.
        # HA injects config_entry as a read-only property automatically.
        return MistralOptionsFlow()


class MistralOptionsFlow(config_entries.OptionsFlow):
    """Options flow — HA injects self.config_entry automatically as a read-only property."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        opts = self.config_entry.options
        current_mode = opts.get(CONF_MODE, DEFAULT_MODE)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                # ── Mode selector ──────────────────────────────────────────
                vol.Required(
                    CONF_MODE,
                    default=current_mode,
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=[
                            selector.SelectOptionDict(value=MODE_MODEL, label="Model (configureer in HA)"),
                            selector.SelectOptionDict(value=MODE_AGENT, label="Agent (geconfigureerd in Mistral Console)"),
                        ],
                        mode=selector.SelectSelectorMode.LIST,
                        translation_key=CONF_MODE,
                    )
                ),

                # ── Agent ID (only used in agent mode) ────────────────────
                vol.Optional(
                    CONF_AGENT_ID,
                    default=opts.get(CONF_AGENT_ID, ""),
                ): selector.TextSelector(
                    selector.TextSelectorConfig(type=selector.TextSelectorType.TEXT)
                ),

                # ── Model settings (only used in model mode) ──────────────
                vol.Optional(
                    CONF_MODEL,
                    default=opts.get(CONF_MODEL, DEFAULT_MODEL),
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=CHAT_MODELS,
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
                vol.Optional(
                    CONF_PROMPT,
                    default=opts.get(CONF_PROMPT, DEFAULT_PROMPT),
                ): selector.TemplateSelector(),
                vol.Optional(
                    CONF_TEMPERATURE,
                    default=opts.get(CONF_TEMPERATURE, DEFAULT_TEMPERATURE),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=0.0, max=1.0, step=0.05,
                        mode=selector.NumberSelectorMode.SLIDER,
                    )
                ),
                vol.Optional(
                    CONF_MAX_TOKENS,
                    default=opts.get(CONF_MAX_TOKENS, DEFAULT_MAX_TOKENS),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=64, max=8192, step=64,
                        mode=selector.NumberSelectorMode.BOX,
                    )
                ),

                # ── Shared settings ───────────────────────────────────────
                vol.Optional(
                    CONF_CONTROL_HA,
                    default=opts.get(CONF_CONTROL_HA, DEFAULT_CONTROL_HA),
                ): selector.BooleanSelector(),

                # ── STT settings ──────────────────────────────────────────
                vol.Optional(
                    CONF_STT_LANGUAGE,
                    default=opts.get(CONF_STT_LANGUAGE, DEFAULT_STT_LANGUAGE),
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=[
                            selector.SelectOptionDict(value=code, label=name)
                            for code, name in LANGUAGE_OPTIONS
                        ],
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
            }),
        )
