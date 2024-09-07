#!/usr/bin/env python
"""The NLP language functionality.

"""

import httpx
import logging
import re
import time

from google.generativeai.types import HarmCategory, HarmBlockThreshold


logger = logging.getLogger(__name__)


class NotAuthenticatedError(Exception):
    pass


class TimeoutException(Exception):
    pass


class NLPClient(object):
    """The general NLP client functionality.

    Subclass for the NLP variants, e.g. using external APIs.

    """

    # Default max tokens to return from the NLP in prompts
    max_tokens = 100  # about 25-50 words?

    def __init__(self, secrets=None, extra=None, modelname=None):
        self.secrets = secrets
        self.modelname = modelname

    def prompt(self, text=None, instructions=None, max_tokens=None):
        """Subclass for the specifig NLP generation.

        Adds the previous dialog to the prompt, for giving context.
        """
        logger.debug("Prompt instruction given: %s", instructions)
        logger.debug("Prompt given: %s", text)

    def convert_to_prompt(self, text, role='user'):
        """Convert text or list with text to the NLP's formats."""
        if isinstance(text, str):
            return text
        return "\n".join(text)


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

    def prompt(self, text=None, instructions=None, max_tokens=None):
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

    def prompt(self, text, instructions=None, max_tokens=None):
        super().prompt(text, instructions)
        text = self.convert_to_prompt(text, role="user")
        if instructions:
            text = instructions + " " + text

        output = self._generate(text, max_tokens=max_tokens)

        # Remove the pretext, so only the new ouptut is returned
        output = output[len(text):].strip()
        logger.debug("Prompt response: %s", output)
        return output

    def _generate(self, pretext, max_tokens=None):
        logger.debug("Generating with prompt: '%s'", pretext)
        logger.debug("Prompt length: %s", len(pretext))

        start = time.time()
        output = self.model.generate(
            pretext, max_length=min(1024, len(pretext) + (max_tokens or
                                                          self.max_tokens))
        ).strip()
        end = time.time()

        logger.debug("Returned answer: %s", output)
        logger.debug("Time elapsed: %.2f seconds", end - start)
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

    def prompt(self, text, instructions=None, max_tokens=None):
        super().prompt(text, instructions)
        text = self.convert_to_prompt(text, role="user")
        if instructions:
            text = instructions + " " + text
        output = self._generate(text, max_tokens=max_tokens)
        return output

    def _generate(self, pretext, max_tokens=None):
        logger.debug("Generating with prompt: '%s'", pretext)
        logger.debug("Prompt length: %s", len(pretext))
        start = time.time()
        raw = self.model(pretext,
                         return_full_text=False,
                         max_new_tokens=max_tokens or self.max_tokens)
        output = raw[0]["generated_text"]
        end = time.time()

        logger.debug("Returned answer: %s", output)
        logger.debug("Time elapsed: %.2f seconds", end - start)
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
        except KeyError:
            pass

        if not api_key or api_key == "CHANGEME":
            raise NotAuthenticatedError(
                "Invalid API key - see " + self.api_key_url)
        return api_key

    def convert_to_prompt(self, text, role='user'):
        """Convert text or list with text to the NLP's formats.

        Using the format that some APIs use:

            {'role': 'system', 'content': 'You are...'},
            {'role': 'user', 'content': 'Could you...'},

        where `role` vary.

        Override in subclasses.

        @param role: Only 'user' and 'system' is supported for now.

        """
        assert role in ('user', 'system')
        if isinstance(text, str):
            text = (text,)
        if isinstance(text, dict):
            text = (text,)
        ret = []
        for t in text:
            if isinstance(t, dict):
                ret.append(t)
            else:
                ret.append({"role": role, "content": t})
        return ret


class MockOnlineNLPClient(OnlineNLPClient):
    """Simulating NLP behaviour of online model"""

    mock_model = "mock-online"

    api_key_url = "https://example.com/api-key"
    secrets_api_key_name = "mock-online-key"

    replies = (
        "The guy asked around.",
        "The girl looked at you.",
        '"What?!" she asked, looking at you.',
        '"Well well well," he said.',
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.modelname:
            self.modelname = self.mock_model
        self.apikey = self._get_api_key()

    def prompt(self, text=None, instructions=None, max_tokens=None):
        super().prompt(text, instructions)
        import random

        response = random.choice(self.replies)
        logger.debug("Prompt response: %s", response)
        return response


class OpenAINLPClient(OnlineNLPClient):
    """NLP models from OpenAI

    https://platform.openai.com/docs/api-reference/chat

    """

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

    def prompt(self, text, instructions=None, max_tokens=None):
        super().prompt(text, instructions)
        # Reformat the prompt to follow OpenAIs specs:
        new_text = []
        if instructions:
            new_text.extend(self.convert_to_prompt(instructions,
                                                   role='system'))
        new_text.extend(self.convert_to_prompt(text))

        starttime = time.time()
        answer = self.client.chat.completions.create(
            model=self.modelname,
            messages=new_text,
            max_tokens=max_tokens or self.max_tokens,
            n=1,
            stream=False,
        )
        logger.debug("Response time: %.3f", time.time() - starttime)
        logger.debug("Prompt response: %s", answer)
        answer = answer.choices[0].message.content
        return answer


class GeminiNLPClient(OnlineNLPClient):
    """NLP models from Google.

    https://ai.google.dev/api/generate-content

    """

    google_model = "gemini-1.5-flash"
    api_key_url = "https://aistudio.google.com/app/apikey"
    secrets_api_key_name = "gemini-key"

    # The sampling temperature, between 0.0 and 1.0.
    # From <https://docs.mistral.ai/api/#tag/chat>:
    # Higher values like 0.8 will make the output more random, while lower
    # values like 0.2 will make it more focused and deterministic. We generally
    # recommend altering this or top_p but not both.

    # Control the randomness of the output. Note: The default value varies by
    # model, see the `Model.temperature` attribute of the `Model` returned the
    # `genai.get_model` function.
    # Values can range from [0.0,1.0], inclusive. A value closer to 1.0 will
    # produce responses that are more varied and creative, while a value closer
    # to 0.0 will typically result in more straightforward responses from the
    # model.
    temperature = 0.75

    # Maximum cumulative probability of tokens to consider when sampling.
    # The Gemini model uses combined Top-k and nucleus sampling.
    #
    # Tokens are sorted based on their assigned probabilities so that only the
    # most likely tokens are considered. Top-k sampling directly limits the
    # maximum number of tokens to consider, while Nucleus sampling limits
    # number of tokens based on the cumulative probability.
    #
    # Note: The default value varies by model, see the `Model.top_p` attribute
    # of the `Model` returned the `genai.get_model` function.
    top_p = 1.0

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
        if not self.modelname:
            self.modelname = self.google_model
        import google.generativeai as genai
        genai.configure(api_key=self._get_api_key())
        logger.debug(f"Model: {self.modelname}")

    def prompt(self, text, instructions=None, max_tokens=None):
        super().prompt(text, instructions)
        import google.generativeai as genai
        generation_config = genai.GenerationConfig(
            candidate_count=1,
            max_output_tokens=max_tokens or self.max_tokens,
            temperature=self.temperature,
            top_p=self.top_p,
        )
        client = genai.GenerativeModel(
            self.modelname,
            safety_settings=self.safety_settings,
            system_instruction=instructions,
            generation_config=generation_config,
        )
        starttime = time.time()
        response = client.generate_content(
            contents=text,
        )
        logger.debug("Response time: %.3f", time.time() - starttime)
        logger.debug("Token usage: %s", response.usage_metadata)
        try:
            answer = response.text
        except ValueError:
            logger.debug(response.prompt_feedback)
            logger.debug("Blocked by Gemini: '%r'", response)
            # TODO: rather raise an exception?
            answer = str(response.prompt_feedback)
            logger.debug("Returning: '%r'", answer)

        logger.debug("Prompt response: %s", answer)
        return answer

    def convert_to_prompt(self, text, role='user'):
        """Convert to Geminis prompt format.

        The format:

            {'role': 'model', 'parts': "You are..."},
            {'role': 'user', 'parts': "Can you..."},

        @param role:
            The 'system' and 'user' is supported. 'system' is converted to
            Geminis 'model'.

        """
        if role == 'system':
            role = 'model'
        if isinstance(text, str):
            text = (text,)
        if isinstance(text, dict):
            text = (text,)
        ret = []
        for t in text:
            if isinstance(t, dict):
                ret.append(t)
            else:
                ret.append({"role": role, "parts": t})
        return ret


class MistralNLP(OnlineNLPClient):
    """NLP models from Mistral.ai.

    https://docs.mistral.ai/api/

    """

    mistral_model = "open-mistral-nemo"
    api_key_url = "https://console.mistral.ai/api-keys/"
    secrets_api_key_name = "mistral-key"

    # Waiting limit when waiting for response from the AIs API
    timeout_ms = 120000

    # The sampling temperature, between 0.0 and 1.0.
    # From <https://docs.mistral.ai/api/#tag/chat>:
    # Higher values like 0.8 will make the output more random, while lower
    # values like 0.2 will make it more focused and deterministic. We generally
    # recommend altering this or top_p but not both.
    temperature = 0.75

    # The top probability tokens to consider
    # From <https://docs.mistral.ai/api/#tag/chat>:
    # Nucleus sampling, where the model considers the results of the tokens
    # with top_p probability mass. So 0.1 means only the tokens comprising the
    # top 10% probability mass are considered. We generally recommend altering
    # this or temperature but not both.
    top_p = 1.0

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from mistralai import Mistral
        self.client = Mistral(api_key=self._get_api_key())
        if not self.modelname:
            self.modelname = self.mistral_model

    def prompt(self, text, instructions=None, max_tokens=None):
        super().prompt(text, instructions)
        # Reformat the prompt to follow Mistrals specs:
        new_text = []
        if instructions:
            new_text.extend(self.convert_to_prompt(instructions,
                                                   role="system"))
        new_text.extend(self.convert_to_prompt(text))

        import mistralai
        try:
            response = self._prompt(new_text, max_tokens=max_tokens)
        except mistralai.models.sdkerror.SDKError as e:
            if e.status_code == 401:
                raise NotAuthenticatedError(e)
            if e.status_code == 429:
                # {"message":"Requests rate limit exceeded"}
                time.sleep(2)
                logger.debug("Requests rate limit exceeded, retrying...")
                # Retry once. Maybe more?
                response = self._prompt(new_text)
            logger.critical(e, exc_info=True)
            raise e
        # TODO: check for limit exceptions
        except httpx.ReadTimeout as e:
            raise TimeoutException(e)

        logger.debug("Token usage: %r", response.usage)
        answer = response.choices[0].message.content
        logger.debug("Prompt response: %s", answer)
        return answer

    def _prompt(self, text, max_tokens=None):
        starttime = time.time()
        response = self.client.chat.complete(
            model=self.modelname,
            messages=text,
            max_tokens=max_tokens or self.max_tokens,
            timeout_ms=self.timeout_ms,
            safe_prompt=False,
            stream=False,
            temperature=self.temperature,
            top_p=self.top_p,
        )
        logger.debug("Response time: %.3f seconds", time.time() - starttime)
        return response

    def convert_to_prompt(self, text, role='user', prefix=False):
        """Convert text or list with text to the NLP's formats.

        Mistral has support for a prefix variable too.

        """
        text = super().convert_to_prompt(text, role)
        if prefix:
            raise Exception("Not implemented")
        return text


nlp_models = {
    "gemini-1.5-flash": GeminiNLPClient,
    "gemini-1.5-pro": GeminiNLPClient,
    "gemini-1.0-pro": GeminiNLPClient,
    "gpt-4o-mini": OpenAINLPClient,
    "gpt-4o": OpenAINLPClient,
    "open-mistral-nemo": MistralNLP,
    "mistral-large-latest": MistralNLP,
    "mock": MockNLPClient,
    "mock-online": MockOnlineNLPClient,
    # TODO: would probably also need a file name
    # "local": LocalNLPClient,
    "huggingface": HuggingfaceNLPClient,
}


def get_nlp_class(model):
    return nlp_models[model]


class NLPHandler(object):
    """Layer between the game and the NLP client.

    Handling the NLP stuff that is not directly part of the client
    functionality.

    """

    default_instructions = """
        % This is the instructions that is given to the AI before the story.
        % - All lines starting with percent (%) are removed for the AI.
        % - Leave the instructions blank to reset to the default instructions.

        You are an excellent story writer assistant, writing remarkable fantasy
        fiction. Do not reply with dialog, only with the answers directly.

        Use markdown format, but use formatting sparsely.

        Writing Guidelines: Use second person perspective and present tense,
        unless the story starts differently. Use writing techniques to bring
        the world and characters to life. Vary what phrases you use. Be
        specific and to the point, and focus on the action in the story. Let
        the characters develop, and bring out their motivations, relationships,
        thoughts and complexity. Keep the story on track, but be creative and
        allow surprising subplots. Include dialog with the characters. Avoid
        repetition and summarisation. Avoid repeating phrases. Use humour.

        If a paragraph starts with "INSTRUCT:", it is not a part of the story,
        but instructions from the user that you must follow when continuing the
        story. Do not add instructions on behalf of the user. Do not include
        the word INSTRUCT in the story.

        """

    def __init__(self, modelname, secrets):
        self.nlp_client = self.load_model(modelname, secrets)

    @staticmethod
    def load_model(modelname, secrets):
        """Instantiate correct NLP model by given input"""
        extra = None
        if ':' in modelname:
            modelname, extra = modelname.split(':', 1)
        # if modelname in ('local', 'huggingface') and extra is None:
        #     raise Exception("Missing param for NLP model, after : in conf")
        logger.debug(f"Loading NLP {modelname!r} with param {extra!r}")
        nlp_class = nlp_models[modelname]
        return nlp_class(secrets=secrets, extra=extra, modelname=modelname)

    def clean_text(self, text):
        """Remove unneccessary white space and other generic mess"""
        if isinstance(text, (list, tuple)):
            return [self.clean_text(t) for t in text]
        # Replace multiple newlines with at most two (keeping paragraphs)
        text = re.sub(r"\n{3,}", "\n\n", text)
        # Replace multiple spaces with a single space
        text = re.sub(r"[ \t\r\f\v]+", " ", text)
        return text

    @staticmethod
    def remove_internal_comments(text):
        """Remove internal comments from given text - lines starting with "%".

        Useful to filter out internal comments before giving it to the AI,
        reducing token usage.

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

    def prompt(self, text, instructions=None, return_raw=False,
               max_tokens=None):
        """Ask the NLP and return the result"""
        # TODO: handle the text in various formats
        if instructions is None:
            instructions = self.default_instructions

        response = self.nlp_client.prompt(
            # TODO: use self.remove_internal_comments on text input too?
            text=self.clean_text(text),
            instructions=self.remove_internal_comments(instructions),
            max_tokens=max_tokens,
        )
        if return_raw:
            return response
        return self.clean_text(response)

    def prompt_for_concept(self):
        """Ask the AI for a random concept for a story and return it."""
        concept = self.prompt(
            """Give me 100-200 words describing an idea for one exiting fantasy
            story. Only return one story. Return a summary of the story,
            including a chapter layout and character descriptions. Do not start
            the story.""", max_tokens=800)
        # TODO; might change this depending on what AI model to use?

        # TODO: Make use of the APIs possibility to fill a object with the
        # proper data. Could then fetch both title, and story details in the
        # same turn.
        return concept

    def prompt_for_title(self, concept_or_summary):
        """Get a title suggestion from the given story concept/summary"""
        title = self.prompt(
            f"""Give me only one title, max 40 characters, for a story with
            the given concept, without any other feedback and no newlines:
            {concept_or_summary}
            """, max_tokens=20)
        # TODO; might change this depending on what AI model to use

        # Some models respond weirdly to this, with a lot of newlines.
        title = title.replace('\n', '')
        title = title[:50]  # Give it some slack, NLPs aren't good at math
        return title

    def prompt_for_introduction(self, game):
        """Get AIs suggestion for the first sentences, starting the story"""
        prompt = ["Give me three sentences that start this story."]
        # TODO: Change this to the prompt model!
        details = self.remove_internal_comments(game.details).strip()
        prompt.append(f"The story has the title: '{game.title}'")
        if details:
            prompt.append("Important details about the story:")
            prompt.append(details)
        return self.prompt(prompt)

    def prompt_for_next_lines(self, game):
        """Get next few lines from the AI, continuing the story.

        @type game: run.Game
        @param game: The game to continue the story from.

        @rtype: str
        @return: A few sentences, from the AI.

        """
        # TODO: Change this to the prompt model!
        prompt = ["Generate two more sentences, continuing the given story:"]
        prompt.append(f"\n---\nThe title of the story: '{game.title}'")

        details = self.remove_internal_comments(game.details).strip()
        if details:
            prompt.append("\n---\nImportant details about the story:")
            prompt.append(details)

        prompt.append("\n---\n<THE-STORY>:\n")
        prompt.extend(game.lines)
        prompt.append("\n\n</THE-STORY>")
        return self.prompt(prompt, instructions=game.instructions)


def main():
    import argparse
    from ai_adventurer import config

    parser = argparse.ArgumentParser(
        description="Run the NLP client directly, for debugging"
    )
    parser.add_argument(
        "-d",
        "--debug",
        action="store_true",
        help="Log debug data to file, for development",
    )
    parser.add_argument(
        "--config-file",
        type=str,
        metavar="FILENAME",
        default=config.default_configfile,
        help="Where the config is located. Default: %(default)s",
    )
    parser.add_argument(
        "--secrets-file",
        type=str,
        metavar="FILENAME",
        default=config.default_secretsfile,
        help="Where the secrets are located. Default: %(default)s",
    )
    parser.add_argument(
        "--nlp-model",
        type=str,
        metavar="MODEL",
        help="Which AI NLP model to use",
    )
    parser.add_argument(
        "--list-nlp-models",
        action="store_true",
        help="List available AI NLP models",
    )

    args = parser.parse_args()

    if args.debug:
        logging.basicConfig(
            filename="logger.log", encoding="utf-8", level=logging.DEBUG
        )
    else:
        logging.basicConfig(
            filename="logger.log", encoding="utf-8", level=logging.WARNING
        )

    if args.list_nlp_models:
        for m in nlp_models:
            print(m)
        return

    configuration = config.load_config(args.config_file, args)
    secrets = config.load_secrets(args.secrets_file)
    modelname = configuration["DEFAULT"]["nlp_model"]

    logger.debug("Starting NLP debug client")
    nlp = NLPHandler(modelname, secrets=secrets)

    def prompt(text, instructions=None):
        print(nlp.prompt(text, instructions=instructions))

    print(f"Using model: {modelname}\n")
    print("Run:\nprompt('This is a prompt')\n")
    print("or look at the nlp object (NLPHandler)\n")

    import code
    import readline
    from rlcompleter import Completer
    readline.parse_and_bind('tab: complete')
    readline.set_completer(Completer(locals()).complete)
    code.interact(local=locals())
    logger.debug("Stopping NLP debug client")


if __name__ == '__main__':
    main()
