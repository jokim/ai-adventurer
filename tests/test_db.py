#!/usr/bin/env python

import pytest

from ai_adventurer import db


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


def test_delete_game(tmp_path):
    db = get_empty_db(tmp_path)
    gameid = db.create_new_game("Test")
    db.delete_game(gameid)
    assert len(db.get_games()) == 0


@pytest.mark.skip("Not implemented yet")
def test_save_lines(tmp_path):
    db = get_empty_db(tmp_path)
    db.create_new_game("Test")
    # TODO: unfinished
