#!/usr/bin/env python
"""The NLP language functionality.

"""

import logging
import time

from google.generativeai.types import HarmCategory, HarmBlockThreshold


logger = logging.getLogger(__name__)


class NotAuthenticatedError(Exception):
    pass


def remove_internal_comments(text):
    """Remove internal comments from given text - lines starting with "%".

    Useful to filter out internal comments before giving it to the AI, reducing
    token usage.

    Example::

        % This is an internal comment, used for helping the end user
        This is the text that the AI language model should care about.

    """
    ret = []
    for line in text.splitlines():
        line = line.lstrip()
        if not line.startswith("%"):
            ret.append(line)
    return "\n".join(ret)


class NLPClient(object):
    """The general NLP client functionality.

    Subclass for the NLP variants, e.g. using external APIs.

    """

    def __init__(self, secrets=None, extra=None, modelname=None):
        self.secrets = secrets
        self.modelname = modelname

    def prompt(self, text=None, instructions=None):
        """Subclass for the specifig NLP generation.

        Adds the previous dialog to the prompt, for giving context.
        """
        if instructions:
            assert isinstance(instructions, str), "Instructions must be string"
        logger.debug("Prompt instruction given: %s", instructions)
        logger.debug("Prompt given: %s", text)


class MockNLPClient(NLPClient):
    """Simulating NLP behaviour"""

    replies = (
        "The guy asked around.",
        "The girl looked at you.",
        '"What?!" she asked, looking at you.',
        '"Well well well," he said.',
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def prompt(self, text=None, instructions=None):
        super().prompt(text, instructions)
        import random

        response = random.choice(self.replies)
        logger.debug("Prompt response: %s", response)
        return response


class LocalNLPClient(NLPClient):
    """NLP prompt executed on a model file generated by keras"""

    def __init__(self, *args, extra=None, **kwargs):
        super().__init__(*args, **kwargs)
        keras_file = extra
        self.model = self._load_model(keras_file)

    def _load_model(self, keras_file):
        import keras
        # import keras_nlp
        model = keras.saving.load_model(keras_file, compile=True)
        return model

    def prompt(self, text, instructions=None):
        super().prompt(text, instructions)

        if isinstance(text, (list, tuple)):
            text = "\n".join(text)
        if instructions:
            text = instructions + " " + text

        output = self._generate(text)

        # Remove the pretext, so only the new ouptut is returned
        output = output[len(text):].strip()
        logger.debug("Prompt response: %s", output)
        return output

    def _generate(self, pretext):
        logger.debug("Generating with prompt: '%s'", pretext)
        logger.debug("Prompt length: %s", len(pretext))

        start = time.time()
        output = self.model.generate(
            pretext, max_length=min(1024, len(pretext) + 40)
        ).strip()
        end = time.time()

        logger.debug("Returned answer: %s", output)
        logger.debug("Time elapsed: %.2f", end - start)
        return output


class HuggingfaceNLPClient(NLPClient):
    """Download a model from HuggingFace and prompt locally"""

    def __init__(self, *args, extra=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.modelid = extra
        self.model = self._load_model(self.modelid)

    def _load_model(self, modelid):
        from transformers import pipeline
        import torch
        logger.debug(f"Try to load HF model {modelid!r}")
        return pipeline("text-generation", model=modelid,
                        model_kwargs={"torch_dtype": torch.bfloat16},
                        device_map="auto")

    def prompt(self, text):
        super().prompt(text)

        if isinstance(text, (list, tuple)):
            text = "\n".join(text)
        output = self._generate(text)
        return output

    def _generate(self, pretext):
        logger.debug("Generating with prompt: '%s'", pretext)
        logger.debug("Prompt length: %s", len(pretext))
        start = time.time()
        raw = self.model(pretext,
                         return_full_text=False,
                         max_new_tokens=30)
        output = raw[0]["generated_text"]
        end = time.time()

        logger.debug("Returned answer: %s", output)
        logger.debug("Time elapsed: %.2f", end - start)
        return output


class OnlineNLPClient(NLPClient):
    """NLP models that uses an online API for prompts."""

    # The URL to where the user could get their API key
    api_key_url = None

    # Name of the key in the DEFAULT section of secrets.ini for the api-key
    secrets_api_key_name = None

    def _get_api_key(self):
        api_key = None
        try:
            api_key = self.secrets["DEFAULT"][self.secrets_api_key_name]
        except TypeError:
            pass

        if not api_key or api_key == "CHANGEME":
            raise NotAuthenticatedError(
                "Invalid API key - see " + self.api_key_url)
        return api_key


class OpenAINLPClient(OnlineNLPClient):
    """NLP models from OpenAI"""

    openai_model = "gpt-4o-mini"

    api_key_url = "https://platform.openai.com/api-keys"
    secrets_api_key_name = "openai-key"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from openai import OpenAI
        self.client = OpenAI(api_key=self._get_api_key())
        if not self.modelname:
            self.modelname = self.openai_model
        logger.debug(f"Model: {self.modelname}")

    def prompt(self, text):
        super().prompt(text)
        # Reformat the prompt to follow OpenAIs specs:
        new_text = []
        for t in text:
            new_text.append({"role": "user", "content": t})

        answer = self.client.chat.completions.create(
            model=self.modelname,
            messages=new_text,
            stream=False,
        )
        logger.debug("Prompt response: %s", answer)
        return answer.choices[0].message.content


class GeminiNLPClient(OnlineNLPClient):
    """NLP models from Google"""

    google_model = "gemini-1.5-flash"

    api_key_url = "https://aistudio.google.com/app/apikey"
    secrets_api_key_name = "gemini-key"

    # Google's tresholds are very sensitive, so need to adjust these. Keep low
    # for now.
    safety_settings = {
        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT:
            HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_HARASSMENT:
            HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_HATE_SPEECH:
            HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT:
            HarmBlockThreshold.BLOCK_NONE,
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        import google.generativeai as genai
        genai.configure(api_key=self._get_api_key())
        if not self.modelname:
            self.modelname = self.google_model

        self.client = genai.GenerativeModel(
            self.modelname, safety_settings=self.safety_settings
        )
        logger.debug(f"Model: {self.modelname}")

    def prompt(self, text):
        super().prompt(text)
        response = self.client.generate_content(
            contents=text,
        )
        try:
            answer = response.text
        except ValueError:
            logger.debug(response.prompt_feedback)
            logger.debug("Blocked by Gemini: '%r'", response)
            answer = str(response.prompt_feedback)
            logger.debug("Returning: '%r'", answer)

        logger.debug("Prompt response: %s", answer)
        return answer


class MistralNLP(OnlineNLPClient):
    """NLP models from Mistral.ai"""

    # Max tokens to return from the AI in prompts
    max_tokens = 400  # about 100-200 words?

    # Waiting limit when waiting for response from the AIs API
    timeout_ms = 20000

    mistral_model = "open-mistral-nemo"
    api_key_url = "https://console.mistral.ai/api-keys/"
    secrets_api_key_name = "mistral-key"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from mistralai import Mistral
        self.client = Mistral(api_key=self._get_api_key())
        if not self.modelname:
            self.modelname = self.mistral_model

    def prompt(self, text):
        super().prompt(text)

        # Reformat the prompt to follow OpenAIs specs:
        new_text = []
        for t in text:
            new_text.append({"role": "user", "content": t})

        logger.debug(f"model {self.modelname}")

        import mistralai
        try:
            response = self.client.chat.complete(
                model=self.modelname,
                messages=new_text,
                max_tokens=self.max_tokens,
                timeout_ms=self.timeout_ms,
                stream=False,
            )
        except mistralai.models.sdkerror.SDKError as e:
            if e.status_code == 401:
                raise NotAuthenticatedError(e)
            logger.critical(e, exc_info=True)
            raise e
        answer = response.choices[0].message.content
        logger.debug("Prompt response: %s", answer)
        return answer


models = {
    "gemini-1.5-flash": GeminiNLPClient,
    "gemini-1.5-pro": GeminiNLPClient,
    "gemini-1.0-pro": GeminiNLPClient,
    "gpt-4o-mini": OpenAINLPClient,
    "gpt-4o": OpenAINLPClient,
    "open-mistral-nemo": MistralNLP,
    "mistral-large-latest": MistralNLP,
    "mock": MockNLPClient,
    # TODO: would probably also need a file name
    # "local": LocalNLPClient,
    "huggingface": HuggingfaceNLPClient,
}

model2apikey = {
    GeminiNLPClient: 'gemini-key',
    OpenAINLPClient: 'openai-key',
    MistralNLP: 'mistral-key',
}


def get_nlp_class(model):
    return models[model]
