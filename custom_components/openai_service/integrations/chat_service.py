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
        self._temperature = entry.options.get("temperature", DEFAULT_TEMPERATURE)

    @property
    def entry(self):
        return self._entry

    @entry.setter
    def entry(self, entry_obj):
        self._entry = entry_obj

    @property
    def response(self) -> str:
        return self._response

    @response.setter
    def response(self, text: str):
        self._response = text

    @property
    def endpoint_type(self) -> str:
        return self._endpoint_type

    @endpoint_type.setter
    def endpoint_type(self, ep_type: str):
        self._endpoint_type = ep_type

    @property
    def model(self) -> str:
        return self._model

    @model.setter
    def model(self, model_string: str):
        self._model = model_string

    @property
    def api_key(self) -> str:
        return self._api_key

    @api_key.setter
    def api_key(self, key: str):
        self._api_key = key

    @property
    def base_url(self):
        return self._base_url

    @base_url.setter
    def base_url(self, url: str):
        self._base_url = url

    @property
    def max_tokens(self) -> int:
        return self._max_tokens

    @max_tokens.setter
    def max_tokens(self, tokens: int):
        self._max_tokens = int(tokens)

    @property
    def mood(self) -> str:
        return self._mood

    @mood.setter
    def mood(self, mood_string: str):
        self._mood = mood_string

    @property
    def temperature(self) -> float:
        return self._temperature

    @temperature.setter
    def temperature(self, temp_float: float):
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
