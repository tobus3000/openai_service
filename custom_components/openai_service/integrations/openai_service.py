"""
The chat completion integration for the openai API.
"""
import logging
from openai import AsyncOpenAI
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import ServiceCall, ServiceResponse
from .chat_service import ChatService  # Adjusted import statement
_LOGGER = logging.getLogger(__name__)

class OpenAIService(ChatService):
    """The OpenAI API chat completion integration.

    Args:
        ChatService (class): The chat completion abstract base class.
    """
    def __init__(self, entry: ConfigEntry):
        """Initialize class and derive parameters from entry object.

        Args:
            entry (ConfigEntry): A Home Assistant `ConfigEntry` object.
        """
        super().__init__(entry)  # Call the __init__ method of the base class
        _LOGGER.debug("OpenAIService Entry data %s", str(entry.data))

    async def chat_completion(self, call: ServiceCall) -> ServiceResponse:
        """Responsible for driving the chat completion with the given input parameters.

        Args:
            call (ServiceCall): The Home Assistant service call object

        Returns:
            ServiceResponse: A dictionary holding the response and other information.
        """
        _LOGGER.debug("OpenAIService Service data %s", str(call.data))
        if self.endpoint_type == "openai":
            client = AsyncOpenAI(api_key=self.api_key)
        elif self.endpoint_type == "custom":
            client = AsyncOpenAI(base_url=self.base_url, api_key=self.api_key)
        messages = [
            {
                "role": "system",
                "content": call.data.get(
                    "mood",
                    self.mood
                ),
            },
            {"role": "user", "content": call.data.get("message")},
        ]
        _LOGGER.debug("OpenAI Service Message: %s", str(messages))
        async with client as client_instance:
            response = await client_instance.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0.6
            )
        self.response = response.choices[0].message.content
        service_response = self.prepare_response()
        _LOGGER.debug("OpenAI Service Response: %s", str(service_response))
        return service_response
