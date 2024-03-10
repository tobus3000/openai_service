"""Config flow for OpenAI Service integration."""
from __future__ import annotations

import logging
from typing import Any

from openai import APIConnectionError, AuthenticationError, OpenAI
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_API_KEY, CONF_NAME, CONF_URL
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError
import homeassistant.helpers.config_validation as cv

from .const import (
    CONF_MAX_TOKENS,
    CONF_MODEL,
    CONF_MOOD,
    CONF_TEMPERATURE,
    DEFAULT_MAX_TOKENS,
    DEFAULT_MODEL,
    DEFAULT_MOOD,
    DEFAULT_NAME,
    DEFAULT_TEMPERATURE,
    DEFAULT_URL,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

OPENAI_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
        vol.Required(CONF_API_KEY): cv.string,
        vol.Optional(CONF_MODEL, default=DEFAULT_MODEL): cv.string,
    }
)

CUSTOM_LLM_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
        vol.Required(CONF_URL, default=DEFAULT_URL): cv.string,
        vol.Optional(CONF_MODEL, default=DEFAULT_MODEL): cv.string,
    }
)


class ConnectionHub:
    """Connection class to verify OpenAI connection."""

    def __init__(self, client: OpenAI) -> None:
        """Initialize."""
        self.client = client

    async def authenticate(self) -> bool:
        """Test if we can authenticate with the API endpoint."""
        try:
            self.client.chat.completions.create(
                model=DEFAULT_MODEL,
                messages=[{"role": "system", "content": "Say this is a test."}],
                max_tokens=5,
            )
        except APIConnectionError as exc:
            raise CannotConnect from exc
        except AuthenticationError as exc:
            raise InvalidAuth from exc
        except Exception as exc:
            raise InvalidAuth from exc
        return True


async def validate_input(
    hass: HomeAssistant, endpoint: str, data: dict[str, Any]
) -> dict[str, Any]:
    """Validate the user input allows us to connect.

    Data has the keys from OPENAI_SCHEMA or
    CUSTOM_LLM_SCHEMA with values provided by the user.
    """
    if endpoint == "openai":
        client = OpenAI(api_key=data.get("api_key"))
    elif endpoint == "custom":
        client = OpenAI(base_url=data.get("url"), api_key="nokey")

    hub = ConnectionHub(client)
    if not await hub.authenticate():
        raise InvalidAuth

    # Return info that you want to store in the config entry.
    return {"endpoint_type": endpoint}


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for OpenAI Service."""

    VERSION = 1
    MINOR_VERSION = 0

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        if user_input is not None:
            pass
        # Will jump to step name in menu_options when selected by user.
        return self.async_show_menu(
            step_id="user",
            menu_options=["openai", "custom"],
            description_placeholders={
                "model": "LLM",
            },
        )

    async def async_step_openai(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                info = await validate_input(self.hass, "openai", user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                user_input.update(info)
                return self.async_create_entry(
                    title=user_input["name"], data=user_input
                )

        return self.async_show_form(
            step_id="openai", data_schema=OPENAI_SCHEMA, errors=errors
        )

    async def async_step_custom(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                info = await validate_input(self.hass, "custom", user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                user_input.update(info)
                return self.async_create_entry(
                    title=user_input["name"], data=user_input
                )

        return self.async_show_form(
            step_id="custom", data_schema=CUSTOM_LLM_SCHEMA, errors=errors
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Create the options flow."""
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handles options flow for the component."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize the Option Flow handler."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options of the OpenAI Service."""

        # Retrieve the options associated with the config entry
        options = self.config_entry.options or {}
        if user_input is not None:
            # Value of data will be set on the options property of our config_entry
            # instance.
            _LOGGER.debug("Saving OpenAI Service options: %s", user_input)
            return self.async_create_entry(
                title="OpenAI Service Options Updated",
                data=user_input,
            )

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_MOOD, default=options.get("mood", DEFAULT_MOOD)
                    ): cv.string,
                    vol.Optional(
                        CONF_TEMPERATURE,
                        default=options.get("temperature", DEFAULT_TEMPERATURE),
                    ): cv.positive_float,
                    vol.Optional(
                        CONF_MAX_TOKENS,
                        default=options.get("max_tokens", DEFAULT_MAX_TOKENS),
                    ): cv.positive_int,
                }
            ),
        )


# Our own exceptions
class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""
