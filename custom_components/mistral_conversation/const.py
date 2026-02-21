"""Constants for the Mistral AI Conversation integration."""

DOMAIN = "mistral_conversation"

# Config keys
CONF_MODEL = "model"
CONF_PROMPT = "prompt"
CONF_MAX_TOKENS = "max_tokens"
CONF_TEMPERATURE = "temperature"
CONF_CONTROL_HA = "control_ha"

# Agent mode
CONF_MODE = "mode"
CONF_AGENT_ID = "agent_id"
MODE_MODEL = "model"
MODE_AGENT = "agent"

# STT
CONF_STT_LANGUAGE = "stt_language"

# Defaults
DEFAULT_MODEL = "mistral-large-latest"
DEFAULT_MAX_TOKENS = 1024
DEFAULT_TEMPERATURE = 0.7   # Mistral range: 0.0–1.0
DEFAULT_CONTROL_HA = True
DEFAULT_MODE = MODE_MODEL
DEFAULT_STT_LANGUAGE = ""   # empty = auto-detect

DEFAULT_PROMPT = (
    "You are a helpful voice assistant for a smart home called {{ ha_name }}.\n"
    "Answer in the same language the user speaks.\n"
    "Be concise and friendly.\n"
    "Today is {{ now().strftime('%A, %B %d, %Y') }}."
)

# Mistral chat models
CHAT_MODELS = [
    "mistral-large-latest",
    "mistral-medium-latest",
    "mistral-small-latest",
    "open-mistral-nemo",
    "open-codestral-mamba",
    "mistral-7b-latest",
]

# STT model
STT_MODEL = "voxtral-mini-latest"

# API
MISTRAL_API_BASE = "https://api.mistral.ai/v1"
