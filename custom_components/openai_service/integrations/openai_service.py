"""
The chat completion integration for the openai API.
"""
import asyncio
from openai import OpenAI, AsyncOpenAI
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import ServiceCall, ServiceResponse
from .chat_service import ChatService  # Adjusted import statement
import logging
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
        if entry.data.get("endpoint_type") == "openai":
            #self.client = OpenAI(api_key=entry.data.get("api_key"))
            self.client = AsyncOpenAI(api_key=entry.data.get("api_key"))
        elif entry.data.get("endpoint_type") == "custom":
            #self.client = OpenAI(base_url=entry.data.get("url"), api_key="nokey")
            self.client = AsyncOpenAI(base_url=entry.data.get("url"), api_key="nokey")

    async def chat_completion(self, call: ServiceCall) -> ServiceResponse:
        """Responsible for driving the chat completion with the given input parameters.

        Args:
            call (ServiceCall): The Home Assistant service call object

        Returns:
            ServiceResponse: A dictionary holding the response and other information.
        """
        _LOGGER.debug("OpenAIService Service data %s", str(call.data))
        messages = [
            {
                "role": "system",
                "content": call.data.get(
                    "mood",
                    self._mood
                ),
            },
            {"role": "user", "content": call.data.get("message")},
        ]
        _LOGGER.debug("OpenAI Service Message: %s", str(messages))
        async with self.client as client_instance:
            response = await client_instance.completions.create(
                model=self._model,
                messages=messages,
                temperature=self._temperature,
                max_tokens=self._max_tokens,
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0.6
            )
        self._response = response.choices[0].text
        # resp = self.client.chat.completions.create(
        #     model=self._entry.data.get("model"),
        #     messages=messages,
        #     #response_format={ "type": "json_object" },
        #     temperature=call.data.get(
        #         "temperature", self._temperature
        #     ),
        #     max_tokens=call.data.get(
        #         "max_tokens", self._max_tokens
        #     ),
        #     top_p=1,
        #     frequency_penalty=0,
        #     presence_penalty=0,
        # )
        # self._response = resp.choices[0].message.content
        service_response = self.prepare_response()
        _LOGGER.debug("OpenAI Service Response: %s", str(service_response))
        return service_response
