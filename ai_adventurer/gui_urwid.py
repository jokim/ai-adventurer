#!/usr/bin/env python
""" The games GUI functionality, using `urwid`.

More features than `blessed`, but still for CLI.

https://urwid.org/

"""

import logging
import subprocess
import tempfile
import time
from collections.abc import Iterable

import urwid

logger = logging.getLogger(__name__)


class GUI(object):
    """The main GUI of the game.

    Now using `urwid` as the GUI engine.

    """

    game_title = "AI adventurer"

    def __init__(self):

        # Build the layout
        self.header_text = urwid.Text(("header", self.game_title),
                                      wrap="ellipsis", align="left")
        self.footer_text = urwid.Text(("footer", "Welcome"),
                                      wrap="ellipsis", align="left")

        self.story_box = StoryBox()
        story_body = urwid.Frame(
            header=urwid.AttrMap(self.header_text, "header"),
            body=urwid.AttrMap(self.story_box, "story"),
            footer=urwid.AttrMap(self.footer_text, "footer"),
        )
        self.loop = urwid.MainLoop(story_body,
                                   self.palette,
                                   unhandled_input=self.unhandled_input)
        self.loop.screen.set_terminal_properties(colors=256)

    def activate(self):
        """Activate fullscreen and start the GUI"""
        # self.load_mainmenu()
        self.loop.run()

    def quit(self, *args):
        raise urwid.ExitMainLoop()

    def unhandled_input(self, key: str) -> None:
        """Handle input that is not handled by widgets?

        Or is this always called? According to urwids docs, I think it always
        comes here first, since it starts at the top?

        """
        if key in {'q', 'Q'}:
            raise urwid.ExitMainLoop()
        # self.header_text.set_text(("header",
        #                            key + " - " + self.game_title))
        logger.debug(f"Unhandled input: {key!r}")

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
        ("reversed", "black,bold", "white", "", "#000,bold", "#fff"),
        ("question", "white,bold", "dark gray", "", "#fff,bold", "#000"),
        # ("streak", "black", "dark red"),
        # ("bg", "white", "dark blue", "", "#fff", "#000"),
    ]

    def set_header(self, text=""):
        if not text:
            text = self.game_title
        else:
            if isinstance(text, (tuple, list)):
                # Could be using urwid formatter format
                text = text[1]
            text = " - ".join((text, self.game_title))
        self.header_text.set_text(("header", text))

    def load_game(self, game, choices):
        """Change the viewer to the game window"""
        self.game = game
        self.set_header(self.game.title)

        self.story_box.choices = choices
        self.story_box.game = game
        self.story_box.load_text()
        story_body = urwid.Frame(
            header=urwid.AttrMap(self.header_text, "header"),
            body=urwid.AttrMap(self.story_box, "story"),
            footer=urwid.AttrMap(self.footer_text, "footer"),
        )
        self.loop.widget = story_body
        # TODO: add listener for the keypresses for this?

    def load_mainmenu(self, choices):
        """Set up and present the main menu.

        Callbacks should be added to the menu options, for starting the
        options.

        """
        def menu_button(caption, callback) -> urwid.AttrMap:
            button = urwid.Button(caption, on_press=callback)
            # TODO: add keypress too somewhere?
            return urwid.AttrMap(button, None, focus_map="reversed")

        def mainmenu(title, choices: Iterable[urwid.Widget]) -> urwid.ListBox:
            body = [urwid.AttrMap(urwid.Padding(urwid.Text(title),
                                                width=("relative", 100)),
                                  "header"),
                    urwid.Divider()]
            for key, choice in choices.items():
                button = menu_button(choice[0], choice[1])
                # TODO: Add key to keypress handler
                body.append(button)
            return urwid.ListBox(urwid.SimpleFocusListWalker(body))

        main = urwid.Padding(mainmenu(("header", "AI adventurer"), choices),
                             left=0, right=0)
        self.body = urwid.Overlay(main,
                                  urwid.SolidFill("\N{MEDIUM SHADE}"),
                                  align=urwid.CENTER,
                                  width=(urwid.RELATIVE, 60),
                                  valign=urwid.MIDDLE,
                                  height=(urwid.RELATIVE, 60),
                                  min_width=20,
                                  min_height=5,
                                  )
        # TODO: add some adventure ornaments - a moving flame, maybe?
        self.loop.widget = self.body

    def load_gamelister(self, games, choices):
        """Load the game overview"""
        body = urwid.Frame(
            header=urwid.AttrMap(self.header_text, "header"),
            body=GameLister(games=games, choices=choices),
            footer=urwid.AttrMap(self.footer_text, "footer"),
        )
        # urwid.SimpleFocusListWalker(gamelist)))
        self.loop.widget = body

    def start_input_edit_text(self, old_text):
        """Ask user to edit given text and return the new one.

        This is calling the external editor, for now at least. Not sure what's
        best option.

        """
        # Just make use of an editor instead
        with tempfile.NamedTemporaryFile(mode="w+", suffix=".txt") as tmpfile:
            tmpfile.write(old_text)
            tmpfile.flush()

            # TODO: Choose your preferred editor, adjust the command
            # accordingly
            editor_command = ["vim", tmpfile.name]
            subprocess.run(editor_command)

            tmpfile.seek(0)
            new_text = tmpfile.read()

        # TODO: sometimes the screen gets weird, not drawn correctly, when
        # returning from the editor (vim at least). Why? Redrawing doesn't seem
        # to work...
        time.sleep(0.5)
        self.loop.draw_screen()
        return new_text

    def start_input_line(self, question="Add a new line: "):
        """Ask the user to write a line"""
        # newline = input(question).strip()
        # return newline

        # TODO: this does not work for now!

        old_body = self.loop.widget

        def on_change(edit: urwid.Edit, new_text: str):
            if "\n" in new_text:
                self.loop.widget = old_body
            # What to do? How to return to correct place?

        body = urwid.Frame(
            # TODO: a function for this?
            header=urwid.AttrMap(self.header_text, "header"),
            body=urwid.AttrMap(urwid.Edit(question), "question"),
            footer=urwid.AttrMap(self.footer_text, "footer"),
        )
        self.loop.widget = body

    def send_message(self, text):
        """Add a message to the user"""
        self.footer_text.set_text(text)


class StoryBox(urwid.Scrollable):
    """The box that handles the story itself."""

    def __init__(self, widget=None, force_forward_keypress=False, game=None):
        self.story_space = urwid.Text("")
        super().__init__(widget=self.story_space,
                         force_forward_keypress=force_forward_keypress)
        self.internal_choices = {
            'j': ('Move down', self.move_pos_down),
            'k': ('Move up', self.move_pos_up),
        }
        if game:
            self.game = game

    def keypress(self, size: 'tuple[int, int]',
                 key: 'str') -> 'str | None':
        logger.debug(f"In StoryBox keypress, with key: {key!r}")
        if key in self.choices:
            logger.debug("Found it!")
            # TODO: add some context with it?
            self.choices[key][1](self)
            return
        elif key in self.internal_choices:
            logger.debug("Found it!")
            # TODO: add some context with it?
            self.internal_choices[key][1]()
            return
        else:
            logger.debug(f"Unhandled key: {key!r}")
        return super().keypress(size, key)

    def move_pos_up(self):
        self.set_scrollpos(self.get_scrollpos() - 10)

    def move_pos_down(self):
        self.set_scrollpos(self.get_scrollpos() + 10)

    def load_text(self):
        """Load in the games story"""
        self.story_space.set_text(" ".join(self.game.lines))


class GameLister(urwid.ListBox):
    """The list of existing stories to load or manage"""

    def __init__(self, games, choices):
        self.internal_choices = {
            'j': ('Move down', self.move_down),
            'k': ('Move up', self.move_up),
        }
        self.choices = choices
        gamelist = []
        for game in games:
            button = urwid.Button(game['title'], on_press=game['callback'],
                                  user_data=game)
            button.gamedata = game
            gamelist.append(urwid.AttrMap(button, None, focus_map="reversed"))
        super().__init__(body=gamelist)

    def keypress(self, size, key):
        logger.debug(f"In GameLister keypress, with key: {key!r}")
        if key in self.choices:
            logger.debug("Found it!")
            # TODO: add some context with it?
            self.choices[key][1](self, focused=self.focus)
            return
        elif key in self.internal_choices:
            logger.debug("Found it!")
            # TODO: add some context with it?
            self.internal_choices[key][1](focused=self.focus)
            return
        else:
            logger.debug(f"Unhandled key: {key!r}")
        return super().keypress(size, key)

    def move_up(self, focused):
        self.set_focus(max(0, self.focus_position - 1))

    def move_down(self, focused):
        self.set_focus(self.focus_position + 1)
