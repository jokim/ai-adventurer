#!/usr/bin/env python

from ai_adventurer import config
from ai_adventurer import db
from ai_adventurer import gui_urwid
from ai_adventurer import nlp
from ai_adventurer import run


# Main controller

def test_controller_load():
    run.Controller(config=config._get_default_config(),
                   secrets=config._get_default_secrets())


def get_mock_controller():
    return run.Controller(config=config._get_default_config(),
                          secrets=config._get_default_secrets())


# Game controller

def test_gamecontroller_load():
    run.GameController(db=db.MockDatabase(),
                       nlp=nlp.NLPHandler("mock",
                                          config._get_default_secrets()),
                       gui=gui_urwid.GUI(),
                       controller=get_mock_controller())


def get_mock_gamecontroller():
    return run.GameController(
        db=db.MockDatabase(),
        nlp=nlp.NLPHandler("mock", config._get_default_secrets()),
        gui=gui_urwid.GUI(),
        controller=get_mock_controller()
    )


def test_start_game():
    gc = get_mock_gamecontroller()
    # gc.start_new_game()
    gc.start_new_game_with_concept(None, "Test")
    print(gc.game.lines)
    assert len(gc.game.lines) > 0
    # TODO: use pytests `patch` and `.assert_called_once`


def test_retry_lines():
    gc = get_mock_gamecontroller()
    # gc.start_new_game()
    gc.start_new_game_with_concept(None, "Test")
    lines = gc.game.lines.copy()
    gc.retry_line(None)
    # TODO: use pytests `patch` and `.assert_called_once`
    assert len(lines) == len(gc.game.lines)


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


# Game object (model)

def test_game_object(tmp_path):
    db = get_empty_db(tmp_path)
    assert len(db.get_games()) == 0
    game = run.Game(db=db)
    assert game.gameid == 1
    assert len(db.get_games()) == 1
    game.save()


def test_game_object_title(tmp_path):
    db = get_empty_db(tmp_path)
    game = run.Game(db=db)
    test_str = "Apple"
    game.set_title(test_str)
    assert game.title == test_str
    assert db.get_games()[0]["title"] == test_str


def test_game_object_details(tmp_path):
    db = get_empty_db(tmp_path)
    game = run.Game(db=db)
    test_str = "This is a story"
    game.set_details(test_str)
    assert game.details == test_str
    assert db.get_games()[0]["details"] == test_str


def test_game_object_instructions(tmp_path):
    db = get_empty_db(tmp_path)
    game = run.Game(db=db)
    test_str = "You are a test"
    game.set_instructions(test_str)
    assert game.instructions == test_str
    assert db.get_games()[0]["instructions"] == test_str


def test_game_object_chunks(tmp_path):
    db = get_empty_db(tmp_path)
    game = run.Game(db=db)
    assert not game.lines
    test_str = "This is a sentence."
    game.add_lines(test_str)
    assert game.lines == [test_str]
    # TODO: check db!


def test_game_copy(tmp_path):
    db = get_empty_db(tmp_path)
    game = run.Game(db=db)
    title = "Test123"
    game.set_title(title)
    instruction = "You are a test"
    game.set_instructions(instruction)
    test_line = "This is a sentence."
    game.add_lines(test_line)
    details = "Very detailed details"
    game.set_details(details)

    newgame = run.Game(db=db)
    newgame.copy_from(game)

    assert newgame.gameid != game.gameid

    assert newgame.title == title
    assert newgame.instructions == instruction
    assert newgame.details == details
    assert newgame.lines == game.lines

    newgame2 = run.Game(db=db, gameid=newgame.gameid)
    assert newgame2.title == title
    assert newgame2.instructions == instruction
    assert newgame2.details == details
    assert newgame2.lines == game.lines
