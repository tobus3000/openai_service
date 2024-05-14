"""
The abstract base class from which the integrations inherit their structure and base functions.
"""
from abc import ABC, abstractmethod
from pysbd import Segmenter
from langid.langid import LanguageIdentifier, model
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import ServiceCall, ServiceResponse
from ..const import DEFAULT_MAX_TOKENS, DEFAULT_MOOD, DEFAULT_TEMPERATURE

class ChatService(ABC):
    """The abstract base class to base chat integrations upon.

    Args:
        ABC (_type_): Define class as an abstract base class by inheriting from `ABC`.
    """
    def __init__(self, entry: ConfigEntry):
        """Initialize class and derive parameters from entry object.

        Args:
            entry (ConfigEntry): A Home Assistant `ConfigEntry` object.
        """
        self.entry = entry
        self.endpoint_type = entry.data.get("endpoint_type", "custom")
        self.response = None
        self.model = entry.options.get("model", "no-model")
        self.api_key = entry.data.get("api_key", "no-key")
        self.base_url = entry.data.get("url")
        self.max_tokens = entry.options.get("max_tokens", DEFAULT_MAX_TOKENS)
        self.mood = entry.options.get("mood", DEFAULT_MOOD)
        self.temperature = entry.options.get("temperature", DEFAULT_TEMPERATURE)

    @property
    def entry(self):
        """Returns the Home Assistant `ConfigEntry` object instance.

        Returns:
            ConfigEntry: `ConfigEntry` object instance
        """
        return self._entry

    @entry.setter
    def entry(self, entry_obj):
        """Store the Home Assistant `ConfigEntry` object instance.

        Args:
            entry_obj (ConfigEntry): `ConfigEntry` object instance.
        """
        self._entry = entry_obj

    @property
    def response(self) -> str:
        """Returns the response text string that was returned from a chat completion.

        Returns:
            str: Chat completion response text.
        """
        return self._response

    @response.setter
    def response(self, text: str):
        """Set the response text that was returned by a chat completion call.

        Args:
            text (str): Chat completion response text.
        """
        self._response = text

    @property
    def endpoint_type(self) -> str:
        """Returns the endpoint type.
        Supported values are:
          - openai
          - custom

        Returns:
            str: The endpoint type. Can be `custom` or `openai`.
        """
        return self._endpoint_type

    @endpoint_type.setter
    def endpoint_type(self, ep_type: str):
        """Set the endpoint type.
        Supported values are:
          - openai
          - custom
        
        Args:
            ep_type (str): The endpoint type. Can be `custom` or `openai`.
        """
        if ep_type in ['custom', 'openai']:
            self._endpoint_type = ep_type
        else:
            self._endpoint_type = "custom"

    @property
    def model(self) -> str:
        """Returns the model to be used by the openai API.
        Not relevant if you run your own LLM locally in most cases.

        Returns:
            str: The model name to be used with the cloud openai endpoint.
        """
        return self._model

    @model.setter
    def model(self, model_string: str):
        """Set the model name to be used with the cloud openai endpoint.

        Args:
            model_string (str): The model name to be used with the cloud openai endpoint.
        """
        self._model = model_string

    @property
    def api_key(self) -> str:
        """Returns the API key to be used with the cloud openai endpoint.
        Not required with a local LLM.

        Returns:
            str: The OpenAI API key.
        """
        return self._api_key

    @api_key.setter
    def api_key(self, key: str):
        """Set the cloud OpenAI API key to be used.

        Args:
            key (str): The OpenAI API key.
        """
        self._api_key = key

    @property
    def base_url(self):
        """Returns the base URL to be used for the chat completion.

        Returns:
            _type_: Base URL like: `http://127.0.0.1:1234/v1
        """
        return self._base_url

    @base_url.setter
    def base_url(self, url: str):
        """Sets the base URL to be used for the chat completion.

        Args:
            url (str): Base URL like: `http://127.0.0.1:1234/v1
        """
        self._base_url = url

    @property
    def max_tokens(self) -> int:
        """Returns the maximum amount of tokens a chat completion
        is allowed to use.

        Returns:
            int: Maximum tokens allowed for chat completion.
        """
        return self._max_tokens

    @max_tokens.setter
    def max_tokens(self, tokens: int):
        """Sets the maximum amount of tokens a chat completion
        is allowed to use.

        Args:
            tokens (int): Maximum tokens allowed for chat completion.
        """
        self._max_tokens = int(tokens)

    @property
    def mood(self) -> str:
        """Returns the 'mood' to be used.
        This is basically the 'prompt' that defines how the LLM should be
        dealing with your question/message.

        Returns:
            str: Returns the 'mood' (aka 'prompt') to be used.
        """
        return self._mood

    @mood.setter
    def mood(self, mood_string: str):
        """Sets the mood to be used.
        This is basically the 'prompt' that defines how the LLM should be
        dealing with your question/message.

        Args:
            mood_string (str): The 'mood' (aka 'prompt') to be used.
        """
        self._mood = mood_string

    @property
    def temperature(self) -> float:
        """Returns the temperature setting of the endpoint.
        Lower values for temperature result in more consistent outputs (e.g. 0.2),
        while higher values generate more diverse and creative results (e.g. 1.0).

        Returns:
            float: The temperature setting of the endpoint.
        """
        return self._temperature

    @temperature.setter
    def temperature(self, temp_float: float):
        """Sets the temperature parameter.
        Lower values for temperature result in more consistent outputs (e.g. 0.2),
        while higher values generate more diverse and creative results (e.g. 1.0).
        Select a temperature value based on the desired trade-off between coherence 
        and creativity for your specific application. The temperature can range is from 0 to 2.

        Args:
            temp_float (float): The temperature setting of the endpoint.
        """
        self._temperature = float(temp_float)

    @abstractmethod
    async def chat_completion(self, call: ServiceCall) -> ServiceResponse:
        """Responsible for driving the chat completion with the given input parameters.

        Args:
            call (ServiceCall): The Home Assistant service call object

        Returns:
            ServiceResponse: A dictionary holding the response and other information.
        """
        self.response= "This is a hard-coded test response from the OpenAI Service integration."
        return self.prepare_response()

    def prepare_response(self) -> dict:
        """Prepares and returns the response of the chat completion.

        Returns:
            dict: Containing the response, it's language and confidence and 
            a list of each sentence, again with language and confidence per sentence.
        """
        overall_lang_guess = ChatService.identify_language(self.response)
        sentences = ChatService.segment_text(self.response, overall_lang_guess[0])
        sentences_classified = ChatService.language_per_sentence(sentences)
        return {
            "response": self.response,
            "language": overall_lang_guess[0],
            "confidence": overall_lang_guess[1],
            "sentences": sentences_classified
        }

    @staticmethod
    def language_per_sentence(sentences: list) -> list:
        """Process a list of sentences and identify the language of each sentence.

        Args:
            sentences (list): The list of strings for which we try to identify the language.

        Returns:
            list: A list of dictionaries where each entry contains the 
            original `text`, the discovered language and the confidence.
        """
        sentences_classified = []
        for s in sentences:
            language = ChatService.identify_language(s)
            sentences_classified.append(
                {
                    "text": s,
                    "language": language[0],
                    "confidence": language[1]
                }
            )
        return sentences_classified

    @staticmethod
    def identify_language(text: str) -> tuple:
        """Takes a string and tries to identify the language of the text.

        Args:
            text (str): The text to find the language for.

        Returns:
            tuple: A tuple of: 2-letter country code and the confidence level.
        """
        identifier = LanguageIdentifier.from_modelstring(model, norm_probs=True)
        return identifier.classify(text)

    @staticmethod
    def segment_text(text: str, language: str = "en") -> list:
        """Segments a piece of text into individual sentences.

        Args:
            text (str): The string that needs to be segmented into sentences.
            language (str, optional): A 2-char country code for better results. Defaults to "en".

        Returns:
            list: A list of strings where each sentence represents an item in the list.
        """
        seg = Segmenter(language=language, clean=False)
        return seg.segment(text)

    def build_messages_payload(self, call: ServiceCall) -> list:
        """Produces a list of dictionaries to be sent in
        the `prompt` or `messages` property or the like.

        Args:
            call (ServiceCall): The Home Assistant service call object

        Returns:
            list: A list containing one dictionary to setup the chat completion.
        """
        return [
            {
                "role": "system",
                "content": call.data.get(
                    "mood",
                    self.mood
                ),
            },
            {"role": "user", "content": call.data.get("message")},
        ]
