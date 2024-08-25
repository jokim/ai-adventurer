#!/usr/bin/env python

import pytest

from ai_adventurer import db


@pytest.mark.skip(reason="Missing implementation")
def test_empty_db(tmp_path):
    path = f"sqlite://{tmp_path}/database.sqlite3"
    print(path)
    db.Database(db_file=path)
