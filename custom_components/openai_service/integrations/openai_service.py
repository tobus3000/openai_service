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
        self.frequency_penalty = 0
        _LOGGER.debug("OpenAIService Entry data %s", str(entry.data))

    @property
    def frequency_penalty(self) -> float:
        """The frequency penalty is a contribution that is proportional 
        to how often a particular token has already been sampled.

        Returns:
            float: Frequency penalty. 0.0-1.0 (max 2.0)
        """
        return float(self._frequency_penalty)

    @frequency_penalty.setter
    def frequency_penalty(self, penalty: float):
        """Set the frequency penalty.
        Reasonable range is: 0.0-1.0
        Negative values can be used to increase the likelihood of repetition

        Args:
            penalty (float): Set the frequency penalty.
        """
        self._frequency_penalty = float(penalty)

    @property
    def presence_penalty(self) -> float:
        """The presence penalty is a one-off additive contribution
        that applies to all tokens that have been sampled at least once.

        Returns:
            float: Presence penalty.
        """
        return float(self._presence_penalty)

    @presence_penalty.setter
    def presence_penalty(self, penalty: float):
        """Set the presence penalty.
        Reasonable range is: 0.0-1.0
        Negative values can be used to increase the likelihood of repetition

        Args:
            penalty (float): Set the presence penalty.
        """
        self._presence_penalty = float(penalty)

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
        async with client as client_instance:
            response = await client_instance.chat.completions.create(
                self.build_completion_payload(call)
            )
        self.response = response.choices[0].message.content
        service_response = self.prepare_response()
        _LOGGER.debug("OpenAI Service Response: %s", str(service_response))
        return service_response

    def build_completion_payload(self, call) -> dict:
        """Returns a dictionary with OpenAI API specific properties.
           Used to run the chat completion.

        Args:
            call (ServiceCall): The Home Assistant service call object

        Returns:
            dict: OpenAI API specific chat completion settings.
        """
        return {
            "model": self.model,
            "messages": self.build_messages_payload(call),
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "top_p": 1,
            "frequency_penalty": self.frequency_penalty,
            "presence_penalty": self.presence_penalty
        }
