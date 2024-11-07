#!/usr/bin/env python

from ai_adventurer import db
from ai_adventurer import run


def test_empty_db(tmp_path):
    print(f"tmp_path: {tmp_path}")
    path = f"sqlite:///{tmp_path}/database.sqlite3"
    print(f"sqlite file: {path}")
    db.Database(db_file=path)


def get_empty_db(tmp_path):
    path = f"sqlite:///{tmp_path}/database.sqlite3"
    return db.Database(db_file=path)


def test_new_game(tmp_path):
    db = get_empty_db(tmp_path)
    assert not db.get_games()
    newgameid = db.create_new_game("Test")
    games = db.get_games()
    assert len(games) == 1
    assert games[0]["title"] == "Test"
    ret = db.get_game(newgameid)
    assert ret["gameid"] == newgameid
    assert ret["title"] == "Test"


def test_new_game_through_model(tmp_path):
    db = get_empty_db(tmp_path)
    g = run.Game(db)
    g.set_title("NewTest")
    games = db.get_games()
    assert len(games) == 1
    assert games[0]["title"] == "NewTest"
    assert games[0]["gameid"] == g.gameid
    ret = db.get_game(g.gameid)
    assert ret["gameid"] == g.gameid
    assert ret["title"] == "NewTest"


def test_delete_game(tmp_path):
    db = get_empty_db(tmp_path)
    gameid = db.create_new_game("Test")
    db.delete_game(gameid)
    assert len(db.get_games()) == 0


def test_save_lines(tmp_path):
    db = get_empty_db(tmp_path)
    g = run.Game(db)
    g.add_lines("One. ")
    g.add_lines("Two. ")
    lines = db.get_lines(g.gameid)
    assert len(lines) == 2
    assert lines == g.lines


def test_get_lines(tmp_path):
    db = get_empty_db(tmp_path)
    g = run.Game(db)
    g.add_lines("Three. ")
    g.add_lines("Four. ")
    g.set_title("One...")
    g.add_lines("Five. ")
    g.add_lines("Six. ")
    g.add_lines("Seven. ")
    g2 = db.get_game(g.gameid)
    assert g2["gameid"] == g.gameid
    assert g2["lines"] == g.lines


def test_get_lines_from_gamelister(tmp_path):
    db = get_empty_db(tmp_path)
    g = run.Game(db)
    g.add_lines("Three. ")
    g.add_lines("Four. ")
    g.set_title("One...")
    g.add_lines("Five. ")
    g.add_lines("Six. ")
    g.add_lines("Seven. ")
    games = db.get_games()
    assert len(games) == 1
    assert games[0]["gameid"] == g.gameid
    assert games[0]["lines"] == g.lines


def test_game_summary(tmp_path):
    db = get_empty_db(tmp_path)
    g = run.Game(db)
    assert g.summary == ""
    newgameid = db.create_new_game("Test of summary")
    ret = db.get_game(newgameid)
    assert ret["summary"] == ""


def test_game_summary_edit(tmp_path):
    db = get_empty_db(tmp_path)
    g = run.Game(db)
    summary = "Just a very short story"
    g.set_summary(summary)
    assert g.summary == summary
    ret = db.get_game(g.gameid)
    assert ret["summary"] == summary


def test_game_max_tokens(tmp_path):
    db = get_empty_db(tmp_path)
    g = run.Game(db)
    g.set_max_token_input(99)
    assert g.max_token_input == 99
    g.set_max_token_output(98)
    assert g.max_token_output == 98

    ret = db.get_game(g.gameid)
    assert ret["max_token_input"] == 99
    assert ret["max_token_output"] == 98
