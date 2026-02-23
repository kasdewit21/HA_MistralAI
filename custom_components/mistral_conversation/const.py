"""Constants for the Mistral AI Conversation integration."""

DOMAIN = "mistral_conversation"

# ---------------------------------------------------------------------------
# Config keys
# ---------------------------------------------------------------------------
CONF_MODEL = "model"
CONF_PROMPT = "prompt"
CONF_MAX_TOKENS = "max_tokens"
CONF_TEMPERATURE = "temperature"
CONF_CONTROL_HA = "control_ha"
CONF_CONTINUE_CONVERSATION = "continue_conversation"
CONF_STT_LANGUAGE = "stt_language"

# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------
DEFAULT_MODEL = "ministral-8b-latest"
DEFAULT_MAX_TOKENS = 1024
DEFAULT_TEMPERATURE = 0.7          # Mistral range: 0.0–1.0
DEFAULT_CONTROL_HA = True
DEFAULT_CONTINUE_CONVERSATION = False
DEFAULT_STT_LANGUAGE = ""          # empty = Voxtral auto-detect

DEFAULT_PROMPT = (
    "You are a helpful voice assistant for a smart home called {{ ha_name }}.\n"
    "Answer in the same language the user speaks.\n"
    "Be concise and friendly.\n"
    "Today is {{ now().strftime('%A, %B %d, %Y') }}."
)

# ---------------------------------------------------------------------------
# Available chat models
# Ordered by suitability for home automation (fast + instruction-following first)
# ---------------------------------------------------------------------------
CHAT_MODELS = [
    "ministral-8b-latest",    # Best for HA: fast, great instruction following, low cost
    "ministral-3b-latest",    # Ultra-fast, lightweight, simple commands
    "mistral-small-latest",   # Balanced: speed + quality
    "mistral-large-latest",   # Most capable, best for complex reasoning
    "open-mistral-nemo",      # Open-source, compact
]

# ---------------------------------------------------------------------------
# STT
# ---------------------------------------------------------------------------
STT_MODEL = "voxtral-mini-latest"

# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------
MISTRAL_API_BASE = "https://api.mistral.ai/v1"
