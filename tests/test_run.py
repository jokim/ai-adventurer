#!/usr/bin/env python

from ai_adventurer import run
from ai_adventurer import db
from ai_adventurer import nlp
from ai_adventurer import config


# Main controller

def test_controller_load():
    run.Controller(config=config._get_default_config(),
                   secrets=config._get_default_secrets())

# Game controller

# TODO

# Game object


def get_empty_db(tmp_path):
    path = f"sqlite:///{tmp_path}/database.sqlite3"
    return db.Database(db_file=path)


def get_fake_secrets():
    return config._get_default_secrets()


def get_mock_handler():
    secrets = get_fake_secrets()
    mock_class = nlp.get_nlp_class('mock-online')
    secrets['DEFAULT'][mock_class.secrets_api_key_name] = 'fake-API-key'
    return nlp.NLPHandler('mock-online', secrets)


def test_game_object(tmp_path):
    db = get_empty_db(tmp_path)
    assert len(db.get_games()) == 0
    game = run.Game(db=db, nlp=get_mock_handler())
    assert game.gameid == 1
    assert len(db.get_games()) == 1
    game.save()


def test_game_object_title(tmp_path):
    db = get_empty_db(tmp_path)
    game = run.Game(db=db, nlp=get_mock_handler())
    test_str = "Apple"
    game.set_title(test_str)
    assert game.title == test_str
    assert db.get_games()[0]["title"] == test_str


def test_game_object_details(tmp_path):
    db = get_empty_db(tmp_path)
    game = run.Game(db=db, nlp=get_mock_handler())
    test_str = "This is a story"
    game.set_details(test_str)
    assert game.details == test_str
    assert db.get_games()[0]["details"] == test_str


def test_game_object_instructions(tmp_path):
    db = get_empty_db(tmp_path)
    game = run.Game(db=db, nlp=get_mock_handler())
    test_str = "You are a test"
    game.set_instructions(test_str)
    assert game.instructions == test_str
    assert db.get_games()[0]["instructions"] == test_str


def test_game_object_chunks(tmp_path):
    db = get_empty_db(tmp_path)
    game = run.Game(db=db, nlp=get_mock_handler())
    assert not game.lines
    test_str = "This is a sentence."
    game.add_lines(test_str)
    assert game.lines == [test_str]
    # TODO: check db!
