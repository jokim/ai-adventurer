#!/usr/bin/env python
"""The database handling

"""

import logging
import sqlite3

logger = logging.getLogger(__name__)

default_db_file = 'data/database.sqlite3'


class Database(object):
    """Handler of game saves.

    """

    def __init__(self, db_file=None):
        if db_file:
            self._db_file = db_file
        else:
            self._db_file = default_db_file

        self._db = sqlite3.connect(self._db_file)


    def get_next_id(self):
        # TODO
        return 235


    def save_game(self, game):
        # TODO: compare lines in db with object, and save differences
        # TODO: Compare and update meatadata, like instructions
        pass


    def add_lines(self, gameid, text):
        """Shortcut to save more text in a game."""
        cu = self._db.cursor()
        #cu.execute("INSERT INTO game_lines WHERE 
        cu.close()
        return True


    def create_db(self):
        # TODO: Fix rest!
        cu = self._db.cursor()
        #cu.execute("CREATE TABLE games(id ID
        #cu.execute("CREATE TABLE game_lines(id ID
        cu.close()
