#!/usr/bin/env python
"""The NLP language functionality.

"""

import logging
import time

from openai import OpenAI

import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold


logger = logging.getLogger(__name__)

default_model = 'data/gpt2base.keras'


class NLPThread(object):
    """The general NLP functionality.

    Subclass for the NLP variants, e.g. using external APIs.

    """

    def __init__(self):
        pass


    def prompt(self, text=None):
        """Subclass for the specifig NLP generation.

        Adds the previous dialog to the prompt, for giving context.
        """
        pass


class MockNLPThread(NLPThread):
    """Simulating NLP behaviour"""

    replies = (
        'The guy asked around.',
        'The girl looked at you.',
        '"What?!" she asked, looking at you.',
        '"Well well well," he said.',
        )

    def __init__(self):
        super().__init__()


    def prompt(self, text=None):
        import random
        response = random.choice(self.replies)
        return response


class LocalNLPThread(NLPThread):
    """NLP prompt thread executed locally.

    Avoids talking with an external API.

    """

    def __init__(self, nlp_file=None):
        import keras
        #import keras_nlp

        super().__init__()

        if not nlp_file:
            nlp_file = default_model
        self.model = self._load_model(nlp_file)


    def _load_model(self, nlp_file):
        import keras
        model = keras.saving.load_model(nlp_file, compile=True)
        return model


    def prompt(self, text):
        super().prompt(text)

        if isinstance(text, (list, tuple)):
            text = '\n'.join(text)

        output = self._generate(text)

        # Remove the pretext, so only the new ouptut is returned
        output = output[len(text):].strip()
        return output


    def _generate(self, pretext):
        logger.debug("Generating with prompt: '%s'", pretext)

        start = time.time()
        output = self.model.generate(
                        pretext,
                        max_length=min(1024, len(pretext) + 40)
        ).strip()
        end = time.time()

        logger.debug("Returned answer: %s", output)
        logger.debug("Time elapsed: %.2f", end - start)
        return output


class OpenAINLPThread(NLPThread):

    openai_model = 'gpt-4o-mini'

    def __init__(self):
        super().__init__()
        # TODO: HACK FIXME: Just shortcutting the OpenAI while testing. Must be
        # a config later!!!
        self.client = OpenAI(api_key='sk-proj-JK9qKvo99lEvhsC8LmQWT3BlbkFJcIsw8NE4kzmwT8B7cn2o')
        # TODO: HACK FIXME: Just shortcutting the OpenAI while testing


    def prompt(self, text):
        # Reformat the prompt to follow OpenAIs specs:
        new_text = []
        for t in text:
            new_text.append({'role': 'user', 'content': t})

        answer = self.client.chat.completions.create(
                    model=self.openai_model,
                    messages=new_text,
                    stream=False,
        )
        return answer.choices[0].message.content


class GeminiNLPThread(NLPThread):

    google_model = 'gemini-1.5-flash'

    # Google's tresholds are very sensitive, so need to adjust these. Keep low for now.
    safety_settings = {
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
    }

    def __init__(self):
        super().__init__()

        # TODO: HACK FIXME: Just shortcutting the api key while testing. Must be
        # a config later!!!
        genai.configure(api_key = 'AIzaSyCcVi-SVhIFl4XOg3ecuM75XC28deo0ozA')
        # TODO: HACK FIXME: Just shortcutting the api key while testing

        self.client = genai.GenerativeModel(self.google_model,
                                            safety_settings=self.safety_settings)


    def prompt(self, text):
        logger.debug("Generating with prompt: '%s'", text)
        answer = self.client.generate_content(
                    contents=text,
        )
        logger.debug("Response from Gemini: '%s'", answer.text)
        return answer.text
