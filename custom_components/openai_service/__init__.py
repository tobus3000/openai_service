"""The OpenAI Service integration."""
from __future__ import annotations

import logging
from openai import OpenAI, AsyncOpenAI
import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import (
    HomeAssistant,
    ServiceCall,
    ServiceResponse,
    SupportsResponse,
    callback,
)
import homeassistant.helpers.config_validation as cv
from .integrations.openai_service import OpenAIService
from .const import DEFAULT_MAX_TOKENS, DEFAULT_MOOD, DEFAULT_TEMPERATURE, DOMAIN

# PLATFORMS: list[Platform] = [Platform.SENSOR]
PLATFORMS: list[Platform] = []
_LOGGER = logging.getLogger(__name__)
CHAT_ITEMS_SERVICE_NAME = "send_request"
CHAT_ITEMS_SCHEMA = vol.Schema(
    {
        vol.Required("message"): cv.string,
        vol.Optional("mood"): cv.string,
        vol.Optional("temperature"): cv.positive_float,
        vol.Optional("max_tokens"): cv.positive_int,
    }
)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up OpenAI Service from a config entry."""

    hass.data.setdefault(DOMAIN, {})
    _LOGGER.debug("OpenAI Service Config data %s", str(entry))

    if entry.data.get("endpoint_type") == "openai":
        client = OpenAI(api_key=entry.data.get("api_key"))
        #client = AsyncOpenAI(api_key=entry.data.get("api_key"))
    elif entry.data.get("endpoint_type") == "custom":
        client = OpenAI(base_url=entry.data.get("url"), api_key="nokey")
        #client = AsyncOpenAI(base_url=entry.data.get("url"), api_key="nokey")
    hass.data[DOMAIN][entry.entry_id] = client
    # Register Options update listener
    entry.async_on_unload(entry.add_update_listener(update_listener))
    openai_service = OpenAIService(entry)

    @callback
    async def chat_completion(call: ServiceCall) -> ServiceResponse:
        """Run chat completion."""
        _LOGGER.debug("OpenAI Service Received data %s", str(call.data))
        _LOGGER.debug("OpenAI Service Entry data %s", str(entry.data))
        return await openai_service.chat_completion(call)

    # Register our service with Home Assistant.
    hass.services.async_register(
        DOMAIN,
        CHAT_ITEMS_SERVICE_NAME,
        chat_completion,
        schema=CHAT_ITEMS_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )

    #    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    # Remove options update_listener.
    # entry_data["unsub_update_listener"]()
    return unload_ok


async def update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update."""
    await hass.config_entries.async_reload(entry.entry_id)
