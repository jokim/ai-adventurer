#!/usr/bin/env python

import pytest

from ai_adventurer import nlp
from ai_adventurer import config


def test_load_base_nlpclient():
    nlp.NLPClient()


def test_all_online_models_load_but_not_authenticate():
    for modelname in nlp.nlp_models:
        model = nlp.get_nlp_class(modelname)
        if issubclass(model, nlp.OnlineNLPClient):
            with pytest.raises(nlp.NotAuthenticatedError):
                model()


def get_fake_secrets():
    return config._get_default_secrets()


def test_all_online_models_load_with_fake_auth():
    secrets = get_fake_secrets()
    for modelname in nlp.nlp_models:
        model = nlp.get_nlp_class(modelname)
        if issubclass(model, nlp.OnlineNLPClient):
            secrets['DEFAULT'][model.secrets_api_key_name] = 'fake-API-key'
            model(secrets=secrets)


def test_load_handler():
    nlp.NLPHandler('mock', get_fake_secrets())


def test_load_handler_online_notauthenticated():
    with pytest.raises(nlp.NotAuthenticatedError):
        nlp.NLPHandler('mock-online', get_fake_secrets())


def test_load_handler_online():
    secrets = get_fake_secrets()
    mock_class = nlp.get_nlp_class('mock-online')
    secrets['DEFAULT'][mock_class.secrets_api_key_name] = 'fake-API-key'
    nlp.NLPHandler('mock-online', secrets)


def get_mock_handler():
    secrets = get_fake_secrets()
    mock_class = nlp.get_nlp_class('mock-online')
    secrets['DEFAULT'][mock_class.secrets_api_key_name] = 'fake-API-key'
    return nlp.NLPHandler('mock-online', secrets)


def test_base_prompt():
    handler = get_mock_handler()
    ret = handler.prompt("What?")
    assert isinstance(ret, str)
    assert len(ret) > 0


def test_base_prompt_with_instructions():
    handler = get_mock_handler()
    ret = handler.prompt("What?", instructions="Reply as a pirate")
    # TODO: get pytest to verify that the internal prompt actually uses the
    # instruction?
    assert isinstance(ret, str)
    assert len(ret) > 0


def test_get_concept():
    handler = get_mock_handler()
    ret = handler.prompt_for_concept()
    assert isinstance(ret, str)
    assert len(ret) > 0


def test_get_title():
    handler = get_mock_handler()
    ret = handler.prompt_for_title("Just a random story")
    assert isinstance(ret, str)
    assert len(ret) > 0


def test_prompt_converter_string():
    test = "This is a string"

    # Base model should only handle text
    nlp_client = nlp.NLPClient()
    ret = nlp_client.convert_to_prompt(test)
    assert ret == test

    # Most online models take a more structured approach
    nlp_client = nlp.OnlineNLPClient()
    ret = nlp_client.convert_to_prompt(test)
    assert ret == [{'role': 'user', 'content': test}]


def test_prompt_converter_strings():
    client = nlp.OnlineNLPClient()
    test = ["This is a string", "Another"]
    ret = client.convert_to_prompt(test)
    assert ret == [{'role': 'user', 'content': test[0]},
                   {'role': 'user', 'content': test[1]}]


def test_prompt_converter_dict():
    client = nlp.OnlineNLPClient()
    test = [{'role': 'system', 'content': "This is a string"}]
    ret = client.convert_to_prompt(test)
    assert ret == test


def test_prompt_converter_dicts():
    test = [
        {'role': 'system', 'content': "This is a string"},
        {'role': 'user', 'content': "Another"},
        {'role': 'system', 'content': "And third"},
    ]
    client = nlp.OnlineNLPClient()
    ret = client.convert_to_prompt(test)
    assert ret == test

# TODO: test changing the format to the different AI APIs format

# TODO: Test the handler more


def test_remove_internal_comments():
    handler = get_mock_handler()
    prompt = ("% This is internal and shall not pass!"
              + "\n"
              + "But this should")
    cleaned = handler.remove_internal_comments(prompt)
    assert cleaned == "But this should"
    assert prompt != cleaned
    assert "This is internal" not in cleaned


def test_remove_internal_comments_but_keep_anything_else():
    handler = get_mock_handler()
    prompt = "This is not internal, but contains a % now and then"
    cleaned = handler.remove_internal_comments(prompt)
    assert cleaned == prompt
    assert "now and then" in cleaned
