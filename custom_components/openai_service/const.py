"""Constants for the OpenAI Service integration."""
DOMAIN = "openai_service"

"""Custom config parameters for this service"""
CONF_MODEL = "model"
CONF_MOOD = "mood"
CONF_TEMPERATURE = "temperature"
CONF_MAX_TOKENS = "max_tokens"

"""Default Config values"""
DEFAULT_NAME = "hassio_openai_service"
DEFAULT_MODEL = "gpt-3.5-turbo-instruct"
DEFAULT_URL = "http://localhost:1234/v1"

"""Default Option values"""
DEFAULT_MOOD = "Your answers are short but precise."
DEFAULT_TEMPERATURE = 0.7
DEFAULT_MAX_TOKENS = 300
