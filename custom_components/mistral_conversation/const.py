"""Constants for the Mistral AI Conversation integration."""

DOMAIN = "mistral_conversation"

CONF_MODEL = "model"
CONF_PROMPT = "prompt"
CONF_MAX_TOKENS = "max_tokens"
CONF_TEMPERATURE = "temperature"
CONF_TOP_P = "top_p"
CONF_CONTROL_HA = "control_ha"

DEFAULT_MODEL = "mistral-large-latest"
DEFAULT_MAX_TOKENS = 1024
DEFAULT_TEMPERATURE = 0.7   # Mistral range: 0.0–1.0
DEFAULT_TOP_P = 1.0
DEFAULT_CONTROL_HA = True

DEFAULT_PROMPT = (
    "You are a helpful voice assistant for a smart home called {{ ha_name }}.\n"
    "Answer in the same language the user speaks.\n"
    "Be concise and friendly.\n"
    "Today is {{ now().strftime('%A, %B %d, %Y') }}."
)

MODELS = [
    "mistral-large-latest",
    "mistral-medium-latest",
    "mistral-small-latest",
    "open-mistral-nemo",
    "open-codestral-mamba",
    "mistral-7b-latest",
]

MISTRAL_API_BASE = "https://api.mistral.ai/v1"
