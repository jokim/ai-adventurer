#!/usr/bin/env python

import pytest

from ai_adventurer import nlp
from ai_adventurer import config


def test_load_base_nlpclient():
    nlp.NLPClient()


def test_all_online_models_load_but_not_authenticate():
    for modelname in nlp.models:
        model = nlp.get_nlp_class(modelname)
        if issubclass(model, nlp.OnlineNLPClient):
            with pytest.raises(nlp.NotAuthenticatedError):
                model()


def get_fake_secrets():
    return config._get_default_secrets()


def test_all_online_models_load_with_fake_auth():
    secrets = get_fake_secrets()
    for modelname in nlp.models:
        model = nlp.get_nlp_class(modelname)
        if issubclass(model, nlp.OnlineNLPClient):
            secrets['DEFAULT'][model.secrets_api_key_name] = 'fakeapi-key'
            model(secrets=secrets)


def test_remove_internal_comments():
    prompt = ("% This is internal and shall not pass!"
              + "\n"
              + "But this should")
    cleaned = nlp.remove_internal_comments(prompt)
    assert cleaned == "But this should"
    assert prompt != cleaned
    assert "This is internal" not in cleaned


def test_remove_internal_comments_but_keep_anything_else():
    prompt = "This is not internal, but contains a % now and then"
    cleaned = nlp.remove_internal_comments(prompt)
    assert cleaned == prompt
    assert "now and then" in cleaned
