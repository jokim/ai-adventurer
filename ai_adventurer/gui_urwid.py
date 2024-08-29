#!/usr/bin/env python
""" The games GUI functionality, using `urwid`.

More features than `blessed`, but still for CLI.

https://urwid.org/

"""

import logging
# import re
# import subprocess
# import tempfile

import urwid

from ai_adventurer import cli_gui

logger = logging.getLogger(__name__)


class GUI(object):
    """The main GUI of the game.

    Now using `urwid` as the GUI engine.

    """

    game_title = "AI adventurer"

    def show_or_exit(self, key: str) -> None:
        if key in {'q', 'Q'}:
            raise urwid.ExitMainLoop()
        self.header_text.set_text(("header",
                                   key + " - " + self.game_title))

    # urwid has a palette in the form of tuples:
    # 1. name of attribute (can be anything I want?)
    # 2. foreground color (16-color)
    # 3. background color
    # 4. monochrome settings (optional)
    # 5. foreground for 88 and 256 colors (optional)
    # 6. background for 88 and 256 colors (optional)
    palette = [
        ("header", "black,bold", "dark blue", "", "#000,bold", "#f90"),
        ("footer", "black,bold", "dark blue", "", "#000,bold", "#f90"),
        ("story", "white", "dark blue", "", "#fff", "#000"),
        ("streak", "black", "dark red"),
        ("bg", "white", "dark blue", "", "#fff", "#000"),
    ]

    def _setup_game_layout(self):
        """Setup the layout of widgets, making up the screen"""
        self.header_text = urwid.Text(("header", self.game_title),
                                      wrap="ellipsis", align="left")
        self.footer_text = urwid.Text(("footer", "Welcome"),
                                      wrap="ellipsis", align="left")

        txt = "No story yet"
        self.story_space = urwid.Text(txt)
        self.story_box = urwid.Scrollable(self.story_space)

        self.body = urwid.Frame(
            header=urwid.AttrMap(self.header_text, "header"),
            body=urwid.AttrMap(self.story_box, "story"),
            footer=urwid.AttrMap(self.footer_text, "footer"),
        )


    def activate(self):
        """Activate fullscreen and start the GUI"""
        self._setup_game_layout()

        loop = urwid.MainLoop(self.body, self.palette,
                              unhandled_input=self.show_or_exit)
        loop.screen.set_terminal_properties(colors=256)
        loop.run()
        cli_gui.UserQuitting()
