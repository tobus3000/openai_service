"""The OpenAI Service integration."""
from __future__ import annotations

import logging

from openai import OpenAI
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

from .const import DEFAULT_MAX_TOKENS, DEFAULT_MOOD, DEFAULT_TEMPERATURE, DOMAIN

# PLATFORMS: list[Platform] = [Platform.TEXT]
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
    elif entry.data.get("endpoint_type") == "custom":
        client = OpenAI(base_url=entry.data.get("url"), api_key="nokey")
    hass.data[DOMAIN][entry.entry_id] = client
    # Register Options update listener
    entry.async_on_unload(entry.add_update_listener(update_listener))

    @callback
    def chat_completion(call: ServiceCall) -> ServiceResponse:
        """Run chat completion."""
        _LOGGER.debug("OpenAI Service Received data %s", str(call.data))
        _LOGGER.debug("OpenAI Service Entry data %s", str(entry.data))
        messages = [
            {
                "role": "assistant",
                "content": call.data.get(
                    "mood",
                    entry.options.get("mood", DEFAULT_MOOD),
                ),
            },
            {"role": "user", "content": call.data.get("message")},
        ]
        _LOGGER.debug("OpenAI Service Message: %s", str(messages))
        resp = client.chat.completions.create(
            model=entry.data.get("model"),
            messages=messages,
            temperature=call.data.get(
                "temperature", entry.options.get("temperature", DEFAULT_TEMPERATURE)
            ),
            max_tokens=call.data.get(
                "max_tokens", entry.options.get("max_tokens", DEFAULT_MAX_TOKENS)
            ),
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
        )
        return {"response": resp.choices[0].message.content}

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
