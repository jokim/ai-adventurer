#!/usr/bin/env python

import pytest

from ai_adventurer import db
from ai_adventurer import config
from ai_adventurer import nlp
from ai_adventurer import run


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


def get_fake_config():
    return config._get_default_config()


def test_all_online_models_load_with_fake_auth():
    secrets = get_fake_secrets()
    for modelname in nlp.nlp_models:
        model = nlp.get_nlp_class(modelname)
        if issubclass(model, nlp.OnlineNLPClient):
            secrets['DEFAULT'][model.secrets_api_key_name] = 'fake-API-key'
            model(secrets=secrets)


def test_load_handler():
    nlp.NLPHandler('mock', get_fake_secrets(), get_fake_config())


def test_load_handler_online_notauthenticated():
    with pytest.raises(nlp.NotAuthenticatedError):
        nlp.NLPHandler('mock-online', get_fake_secrets(), get_fake_config())


def test_load_handler_online():
    secrets = get_fake_secrets()
    mock_class = nlp.get_nlp_class('mock-online')
    secrets['DEFAULT'][mock_class.secrets_api_key_name] = 'fake-API-key'
    nlp.NLPHandler('mock-online', secrets, get_fake_config())


def get_mock_handler():
    """Return a mock NLPHandler"""
    secrets = get_fake_secrets()
    mock_class = nlp.get_nlp_class('mock-online')
    secrets['DEFAULT'][mock_class.secrets_api_key_name] = 'fake-API-key'
    return nlp.NLPHandler('mock-online', secrets, get_fake_config())


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


def get_mock_db(tmp_path):
    """Get temp, empty sqlite db for mocking"""
    path = f"sqlite:///{tmp_path}/database.sqlite3"
    return db.Database(db_file=path)


def get_mock_gameobj(tmp_path):
    db = get_mock_db(tmp_path)
    return run.Game(db=db)


def test_handler_get_next_line(tmp_path):
    game = get_mock_gameobj(tmp_path)
    handler = get_mock_handler()
    ret = handler.prompt_for_next_lines(game)
    assert ret
    ret = handler.prompt_for_next_lines(game)
    assert ret


def test_handler_autosummarize(tmp_path, mocker):
    game = get_mock_gameobj(tmp_path)
    game.add_lines("Test1.")
    game.add_lines("Test2.")
    game.add_lines("Test3.")

    handler = get_mock_handler()
    handler.limit_story_prompt_characters = 5
    spy = mocker.spy(handler, "prompt_for_ai_summary")

    ret = handler.prompt_for_next_lines(game)
    assert ret
    spy.assert_called_once()
    assert game.summary_ai


def test_handler_autosummarize_continously(tmp_path, mocker):
    game = get_mock_gameobj(tmp_path)
    game.add_lines("Test1.")
    game.add_lines("Test2.")
    game.add_lines("Test3.")

    handler = get_mock_handler()
    handler.limit_story_prompt_characters = 2
    spy = mocker.spy(handler, "prompt_for_ai_summary")
    handler.prompt_for_next_lines(game)
    spy.assert_called_once()
    mocker.stop(spy)
    assert game.summary_ai != ""
    prev_ai_line = game.summary_ai_until_line

    game.add_lines("Test4.")
    game.add_lines("Test5.")
    game.add_lines("Test6.")
    spy = mocker.spy(handler, "prompt_for_ai_summary")
    handler.prompt_for_next_lines(game)
    spy.assert_called_once()
    assert game.summary_ai_until_line > prev_ai_line


def test_remove_internal_comments():
    handler = get_mock_handler()
    prompt = ("§ This is internal and shall not pass!"
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
