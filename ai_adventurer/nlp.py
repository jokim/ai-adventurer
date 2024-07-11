#!/usr/bin/env python
"""The NLP language functionality.

"""

import logging
import time

#import keras_nlp
import keras

default_model = 'data/gpt2base.keras'


class NLP(object):
    """The NLP functionality"""

    start_prompt = "This is a story. "

    def __init__(self, nlp_file=None):
        if not nlp_file:
            nlp_file = default_model
        self.model = self._load_model(nlp_file)


    def _load_model(self, nlp_file):
        model = keras.saving.load_model(nlp_file, compile=True)
        return model


    def generate(self, pretext=""):
        """Return a generated sentence."""
        if isinstance(pretext, (tuple, list)):
            pretext = '\n'.join(pretext)
        start = time.time()
        output = self.model.generate(' '.join((self.start_prompt, pretext)),
                                     max_length=20)
        end = time.time()
        logging.debug(f"TOTAL TIME ELAPSED: {end - start:.2f}s")
        return output
