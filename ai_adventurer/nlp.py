#!/usr/bin/env python
"""The NLP language functionality.

"""

import logging
import time
import random

from openai import OpenAI

import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold


logger = logging.getLogger(__name__)

default_model = 'data/gpt2base.keras'


class NLPThread(object):
    """The general NLP functionality.

    An object is keeping track of a single prompt thread.

    Subclass for the NLP variants, e.g. using external APIs.

    """

    def __init__(self):
        self.dialog = []


    def add_dialog(self, text, role):
        """Add text or instructions to the dialog.

        A new prompt is not generated yet. Use `prompt()` for that."""
        self.dialog.append({'role': role, 'content': text})


    def prompt(self, text=None, role='user'):
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
        import random
        super().__init__()


    def prompt(self, text=None, role='user'):
        self.add_dialog(text, role=role)
        response = random.choice(self.replies)
        # TODO: OpenAI calls itself 'assistant', while Google calls it 'model'
        # and vice versa with 'content' vs 'parts'
        self.add_dialog(response, role='model')
        return response


class LocalNLPThread(NLPThread):
    """NLP prompt thread executed locally.

    Avoids talking with an external API.

    """

    def __init__(self, nlp_file=None):
        #import keras_nlp
        import keras

        super().__init__()

        if not nlp_file:
            nlp_file = default_model
        self.model = self._load_model(nlp_file)


    def _load_model(self, nlp_file):
        model = keras.saving.load_model(nlp_file, compile=True)
        return model


    def prompt(self, text, role='user'):
        super().prompt(text, role=role)
        self.add_dialog(text, role=role)

        context = []
        for line in self.dialog:
            context.append(line['content'])
        
        context = '\n'.join(context)
        output = self._generate(context)

        # Remove the pretext, so only the new ouptut is returned
        output = output[len(context):].strip()
        self.add_dialog(output, role='model')
        return output


    def generate(self, pretext=""):
        """Return a generated sentence."""
        if isinstance(pretext, (tuple, list)):
            pretext = '\n'.join(pretext).strip()
        if not pretext:
            pretext = ' '.join((self.start_prompt, pretext)).strip()

        output = self._generate(pretext)
        # Remove pretext
        output = output[len(pretext):].strip()
        logger.debug("New text: %s", output)
        return output.strip()


    def _generate(self, pretext):
        logger.debug("Generating with prompt: '%s'", pretext)

        start = time.time()
        output = self.model.generate(
                        pretext,
                        max_length=min(1024, len(pretext) + 50)
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

    def prompt(self, text, role='user'):
        self.add_dialog(text=text, role=role)

        # TODO: make use of the stream functionality
        answer = self.client.chat.completions.create(
                    model=self.openai_model,
                    messages=self.dialog,
                    stream=False,
        )

        self.add_dialog(role='model', text=answer.choices[0].message.content)
        return answer.choices[0].message.content


class GeminiNLPThread(NLPThread):

    google_model = 'gemini-1.5-flash'

    # Google's tresholds are very sensitive, so need to adjust these. Keep low for now.
    safety_settings = {
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_UNSPECIFIED: HarmBlockThreshold.BLOCK_NONE,
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


    def prompt(self, text, role='user'):
        self.add_dialog(text=text, role=role)

        # TODO: make use of the stream functionality
        answer = self.client.generate_content(
                    contents=self.dialog,
                    stream=False,
        )
        self.add_dialog(role='model', text=answer.text)
        return answer.text
