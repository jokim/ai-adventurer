# AI adventurer

A tiny CLI story helper game, making use of AI (NLP) prompts to generate next
events in a story you and the AI create.

Don't expect much, as this is written most for me to get an understanding of
AI.

The game is set up to talk with OpenAI (GPT4o) and Googles Gemini. You need API
keys to make use of it. I also tested local AI models, but the model is not
included. Go see HuggingFace or Keras for that.


## Setup

```
poetry install
poetry run ai_adventurer/run.py --list-nlp-models
```

To also make use of models from HuggingFace, i.e. download them and use them
locally, you also need to include the `localai` group:

```
poetry install --with localai
```

### Configuration

If you start the game and push 'c' in the start menu, it will create two files:
`config.ini` and `secrets.ini` (for API keys).


### Testing

Tests can be run with:

```
poetry run pytest
```

