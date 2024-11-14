#!/usr/bin/env python
"""The database handling

"""

from typing import List
from typing import Optional
import logging
import tempfile

import sqlalchemy
import sqlalchemy.orm as orm
from sqlalchemy import String, Integer


logger = logging.getLogger(__name__)

default_db_file = "sqlite:///data/database.sqlite3"


class _Base(orm.DeclarativeBase):
    pass


class Game(_Base):
    __tablename__ = "games"

    gameid: orm.Mapped[int] = orm.mapped_column(primary_key=True)
    title: orm.Mapped[Optional[str]]

    """The instructions to give to the AI NLP"""
    instructions: orm.Mapped[Optional[str]]

    """The story details, controlling how the story should go"""
    details: orm.Mapped[Optional[str]]

    """A summary of the story (ideally dynamically updated by the NLP)"""
    summary: orm.Mapped[str] = orm.mapped_column(String, default='')

    """A summary of the story for the NLP (dynamically updated by the NLP)"""
    summary_ai: orm.Mapped[str] = orm.mapped_column(String, default='')

    """What line the summary has been generated to"""
    summary_ai_until_line: orm.Mapped[int] = orm.mapped_column(Integer,
                                                               default=0)
    # TODO: Should it rather look at the number of tokens instead?

    """A token limit per story interaction to fetch to the NLP model"""
    max_token_output: orm.Mapped[Optional[int]]

    """Max tokens to feed the NLP. Longer stories must e.g. be summarized."""
    max_token_input: orm.Mapped[Optional[int]]

    """The story itself"""
    lines: orm.Mapped[List["Line"]] = orm.relationship(
        back_populates="game", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"Game(id={self.gameid!r}, title={self.title!r})"


class Line(_Base):
    __tablename__ = "lines"

    gameid: orm.Mapped[int] = orm.mapped_column(
        sqlalchemy.ForeignKey("games.gameid"),
        primary_key=True,
    )
    lineid: orm.Mapped[int] = orm.mapped_column(
        primary_key=True,
    )
    text: orm.Mapped[Optional[str]]

    game: orm.Mapped["Game"] = orm.relationship(back_populates="lines")

    def __repr__(self) -> str:
        ret = f"Line(game={self.gameid!r}, line={self.lineid!r}"
        if self.text:
            ret += f", text={self.text[:20]!r}…"
        ret += ")"

        return ret


class Database(object):
    """Handler of game saves."""

    def __init__(self, db_file=None):
        if db_file:
            self._db_file = db_file
        else:
            self._db_file = default_db_file

        self._engine = sqlalchemy.create_engine(self._db_file)
        _Base.metadata.create_all(self._engine, checkfirst=True)

    def create_new_game(self, title=""):
        """Create a new game in the db"""
        with orm.Session(self._engine) as session:
            game = Game(title=title)
            session.add(game)
            session.commit()
            return game.gameid

    def delete_game(self, gameid):
        """Delete a given game from the db.

        TODO: In the future, might rather want to tag it as deleted, to be able
        to undelete it later?

        """
        assert isinstance(gameid, int)
        with orm.Session(self._engine) as session:
            game = self._get_game(gameid, _session=session)
            session.delete(game)
            session.commit()

    def _get_game(self, gameid, _session=None):
        """Get a game object for the given gameid"""
        if not _session:
            _session = orm.Session(self._engine)
        for game in _session.scalars(
            sqlalchemy.select(Game).where(Game.gameid == gameid)
        ):
            return game

    def _convert_lines(self, dblines):
        """Get a simpler, sorted list with lines, without its metadata"""
        lines = []
        for line in sorted(dblines, key=lambda k: k.lineid):
            # TODO: make sure it's sorted!
            lines.append(line.text)
        return lines

    def get_game(self, gameid, _session=None):
        """Get a given games data"""
        game = self._get_game(gameid=gameid, _session=_session)
        return {
            "gameid": game.gameid,
            "title": game.title,
            "instructions": game.instructions,
            "details": game.details,
            "lines": self._convert_lines(game.lines),
            "max_token_input": game.max_token_input,
            "max_token_output": game.max_token_output,
            "summary": game.summary,
            "summary_ai": game.summary_ai,
            "summary_ai_until_line": game.summary_ai_until_line,
        }
        # How to also return Lines for the given Game?

    def get_games(self, _session=None):
        """Get a list of games"""
        if not _session:
            _session = orm.Session(self._engine)
        ret = []
        for game in _session.scalars(sqlalchemy.select(Game)):
            ret.append(
                {
                    "gameid": game.gameid,
                    "title": game.title,
                    "instructions": game.instructions,
                    "details": game.details,
                    "lines": self._convert_lines(game.lines),
                    "max_token_input": game.max_token_input,
                    "max_token_output": game.max_token_output,
                    "summary": game.summary,
                    "summary_ai": game.summary_ai,
                    "summary_ai_until_line": game.summary_ai_until_line,
                }
            )
        return ret

    def get_lines(self, gameid, _session=None):
        """Get all lines, or story chunks, from a given game"""
        if not _session:
            _session = orm.Session(self._engine)
        ret = []
        for line in _session.scalars(
            sqlalchemy.select(Line).where(Line.gameid == gameid)
        ):
            ret.append(line.text)
        return ret

    def save_game(self, game):
        """Save given game data to the db, including its lines.

        @type game: ai_adventurer.db.Game
        @param game: The game object to save.

        """
        session = orm.Session(self._engine)
        db_game = self._get_game(game.gameid, _session=session)

        db_game.instructions = game.instructions
        db_game.title = game.title
        db_game.details = game.details
        db_game.summary = game.summary
        db_game.summary_ai = game.summary_ai
        db_game.summary_ai_until_line = game.summary_ai_until_line
        if hasattr(game, "max_token_input"):
            db_game.max_token_input = game.max_token_input
        if hasattr(game, "max_token_output"):
            db_game.max_token_output = game.max_token_output

        # This blindly overwrites the existing lines. Probably a better way.
        line_struct = []
        for lineno, line in enumerate(game.lines):
            line_struct.append(
                Line(
                    gameid=db_game.gameid,
                    lineid=lineno,
                    text=line,
                )
            )

        db_game.lines = line_struct
        session.commit()


class MockDatabase(Database):
    """Mocking the database by creating a temp sqlite file."""

    def __init__(self, db_file=None):
        mock_fd, mock_filename = tempfile.mkstemp(suffix='.sqlite')
        path = "sqlite:///" + mock_filename
        super().__init__(db_file=path)
