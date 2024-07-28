#!/usr/bin/env python
"""The database handling

"""

from typing import List
from typing import Optional
import logging
import sqlite3

import sqlalchemy
import sqlalchemy.orm as orm


logger = logging.getLogger(__name__)

default_db_file = 'sqlite:///data/database.sqlite3'


class _Base(orm.DeclarativeBase):
    pass


class Game(_Base):
    __tablename__ = 'games'

    gameid: orm.Mapped[int] = orm.mapped_column(primary_key=True)
    title: orm.Mapped[Optional[str]]
    instructions: orm.Mapped[Optional[str]]
    details: orm.Mapped[Optional[str]]

    lines: orm.Mapped[List["Line"]] = orm.relationship(
        back_populates="game",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"Game(id={self.gameid!r}, title={self.title!r})"


class Line(_Base):
    __tablename__ = 'lines'

    gameid: orm.Mapped[int] = orm.mapped_column(
        sqlalchemy.ForeignKey('games.gameid'),
        primary_key=True,
    )
    lineid: orm.Mapped[int] = orm.mapped_column(
        primary_key=True,
    )
    text: orm.Mapped[Optional[str]]

    game: orm.Mapped["Game"] = orm.relationship(
            back_populates="lines"
    )

    def __repr__(self) -> str:
        ret = f"Line(game={self.gameid!r}, line={self.lineid!r}"
        if self.text:
            ret += f", text={self.text[:20]!r}…"
        ret += ')'

        return ret


class Database(object):
    """Handler of game saves.

    """

    def __init__(self, db_file=None):
        if db_file:
            self._db_file = db_file
        else:
            self._db_file = default_db_file

        self._engine = sqlalchemy.create_engine(self._db_file)
        _Base.metadata.create_all(self._engine)


    def create_new_game(self, title=''):
        with orm.Session(self._engine) as session:
            game = Game(title=title)
            session.add(game)
            session.commit()
            return game.gameid


    def _get_game(self, gameid, _session=None):
        if not _session:
            _session = orm.Session(self._engine)
        for game in _session.scalars(sqlalchemy.select(Game)
                                        .where(Game.gameid == gameid)):
            return game


    def get_game(self, gameid, _session=None):
        game = self._get_game(gameid=gameid, _session=_session)
        return {
            'gameid': game.gameid,
            'title': game.title,
            'instructions': game.instructions,
            'details': game.details,
        }


    def save_game(self, game):
        session = orm.Session(self._engine)
        db_game = self._get_game(game.gameid, _session=session)

        db_game.instructions = game.instructions
        db_game.title = game.title
        db_game.details = game.details

        # This blindly overwrites the existing lines. Probably a better way.
        line_struct = []
        for lineno, line in enumerate(game.lines):
            line_struct.append(Line(
                gameid=db_game.gameid,
                lineid=lineno,
                text=line,
            ))

        db_game.lines = line_struct
        session.commit()
