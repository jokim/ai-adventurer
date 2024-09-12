#!/usr/bin/env python
""" The games GUI functionality, using `urwid`.

More features than `blessed`, but still for CLI.

https://urwid.org/

"""

import logging
import random
import re
import string
import subprocess
import tempfile
import textwrap
import threading
import time

import urwid

from ai_adventurer import textutils as tu

logger = logging.getLogger(__name__)


class GUI(object):
    """The main GUI of the game.

    Now using `urwid` as the GUI engine.

    """

    game_title = "AI adventurer"

    def __init__(self):

        # Build the layout
        self.header_text = urwid.Text(("header", self.game_title),
                                      wrap="ellipsis", align="center")
        self.footer_text = urwid.Text(("footer", "Welcome"),
                                      wrap="ellipsis", align="center")
        self.event_reset = threading.Event()
        self.loop = urwid.MainLoop(urwid.Text(""),
                                   self.palette,
                                   unhandled_input=self.unhandled_input,
                                   pop_ups=True)
        self.loop.screen.set_terminal_properties(colors=256)

    def activate(self):
        """Activate fullscreen and start the GUI"""
        self.loop.run()

    def quit(self, *args, **kwargs):
        self.event_reset.set()
        raise urwid.ExitMainLoop()

    def unhandled_input(self, key: str) -> None:
        """Handle input that is not handled by widgets?

        Or is this always called? According to urwids docs, I think it always
        comes here first, since it starts at the top?

        """
        if key == "ctrl d":
            # TODO: This is a hack, since I don't know how to enforce that the
            # popup' keypress function is used...
            if hasattr(self.loop.widget, 'close_pop_up'):
                self.loop.widget.close_pop_up()
        if key in {'q', 'Q'}:
            self.quit()
        logger.debug(f"In main GUI: Unhandled input: {key!r}")

    # urwid has a palette in the form of tuples:
    # 1. name of attribute (can be anything I want?)
    # 2. foreground color (16-color)
    # 3. background color
    # 4. monochrome settings (optional)
    # 5. foreground for 88 and 256 colors (optional)
    # 6. background for 88 and 256 colors (optional)
    palette = [
        ("header", "black,bold", "brown", "", "black,bold", "brown"),
        ("title",  "black,bold", "brown", "", "black,bold", "brown"),
        ("footer", "black,bold", "brown", "", "black,bold", "brown"),
        ("story", "white", "", "", "#fff", ""),
        ("selected", "black", "white", "", "#000", "#fff"),
        ("reversed", "black,bold", "white", "", "#000,bold", "#fff"),
        ("question", "white,bold", "dark gray", "", "#fff,bold", "#000"),
        ("chapter", "black,bold", "brown", "", "#000,bold", "brown"),
        ("instruction", "light gray", "dark gray", "", "dark gray", "#222"),
        ("flame", "light red", "", "", "light red", ""),
        # ("streak", "black", "dark red"),
        # ("bg", "white", "dark blue", "", "#fff", "#000"),
    ]

    def set_header(self, text=""):
        if not text:
            text = self.game_title
        else:
            if isinstance(text, (tuple, list)):
                # Could be using urwid formatter format, which we don't want
                text = text[1]
            text = " - ".join((text, self.game_title))
        self.header_text.set_text(("header", text))

    def _get_body(self, body, footer=True):
        """Generate the main content of the screen"""
        if footer:
            footer = urwid.AttrMap(self.footer_text, "footer")
        else:
            footer = None

        return urwid.Frame(
            header=urwid.AttrMap(self.header_text, "header"),
            body=body,
            footer=footer
        )

    def set_body(self, body, footer=True):
        self.loop.widget = self._get_body(body=body, footer=footer)

    def load_game(self, game, choices):
        """Change the viewer to the game window"""
        self.event_reset.set()
        self.set_header(game.title)
        self.story_box = StoryBox(game=game, choices=choices)
        # TODO: When adding the ScrollBar, I got out of bounds exceptions from
        # urwid.widget.widget.validate_size(). Why?
        # body = urwid.ScrollBar(
        #     urwid.Padding(self.story_box, right=2),
        #     thumb_char=urwid.ScrollBar.Symbols.LITE_SHADE,
        #     width=1,
        # )
        self.set_body(urwid.Padding(
            # body,
            self.story_box,
            align="center",
            width=73,
        ))

    def load_mainmenu(self, choices):
        """Set up and present the main menu.

        Callbacks should be added to the menu options, for starting the
        options.

        """
        self.event_reset.set()
        self.set_header("Main menu")
        main = urwid.Padding(MainMenu(choices=choices), left=0, right=0)

        flamewidgets = (
            ('weight', 10, Flame()),
            ('weight', 80, urwid.Padding(urwid.Text(""))),
            ('weight', 10, Flame()),
        )

        def regenerate_flames(*args, **kwargs):
            for f in flamewidgets:
                if isinstance(f[2], Flame):
                    f[2].regenerate_flame()
            self.loop.draw_screen()

        def regenerate_flame_loop(stop_event):
            time.sleep(0.1)
            while not stop_event.is_set():
                regenerate_flames()
                time.sleep(0.1 + random.random())  # 0.1 - 1.1 seconds

        background = urwid.Filler(urwid.Columns(flamewidgets, dividechars=3),
                                  valign=("relative", 98))
        body = urwid.Overlay(main,
                             background,
                             align=urwid.CENTER,
                             width=(urwid.RELATIVE, 40),
                             valign=urwid.MIDDLE,
                             height=(urwid.RELATIVE, 30),
                             min_width=20,
                             min_height=5,
                             )
        self.set_body(body, footer=False)

        self.event_reset.clear()
        self.flame_thread = threading.Thread(target=regenerate_flame_loop,
                                             args=(self.event_reset,))
        self.flame_thread.start()

    def load_gamelister(self, games, choices):
        """Load the game overview"""
        self.event_reset.set()
        # urwid.SimpleFocusListWalker(gamelist)))
        self.set_body(GameLister(games=games, choices=choices))

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

        # Force redrawing the screen. I guess editors write back the old
        # buffer, making urwid look weird.
        self.loop.screen.clear()
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

    def ask_confirm(self, question="Are you sure?", callback=None,
                    user_data=None):
        """Ask the user to confirm something.

        If the user confirms, the callback is called. Otherwise the popup is
        removed and it's back to the previous screen.

        """
        launch = ConfirmPopupLauncher(self.loop.widget, question=question,
                                      callback=callback, user_data=user_data)
        self.loop.widget = launch
        launch.open_pop_up()

    def ask_oneliner(self, question="Give input: ", callback=None,
                     user_data=None, existing_text=""):
        """Ask the user to confirm something.

        If the user confirms, the callback is called. Otherwise the popup is
        removed and it's back to the previous screen.

        """
        editer = InputWindow(self.loop.widget, question=question,
                             callback=callback, edit_text=existing_text)
        self.loop.widget = editer
        editer.open_pop_up()


class Menu(urwid.ListBox):
    """A Lister widget, for handling choices to the list"""

    def __init__(self, choices):
        """Init

        @param title: The title of the menu

        @param choices:
            The items in the menu. Should be a dict in the format:

                'keyboard-key': ("Name of element", callback-func),

        """
        self.choices = choices
        self.internal_choices = {
            'j': self.move_down,
            'k': self.move_up,
        }
        self.body = self.generate_body()
        super().__init__(urwid.SimpleFocusListWalker(self.body))

    def generate_body(self):
        """Return the body content of the Menu. Subclass to override."""
        body = []
        for key, choice in self.choices.items():
            button = self.generate_menu_item(f"{key:>4} - {choice[0]}",
                                             choice[1])
            body.append(button)
        return body

    def regenerate_body(self):
        """Update the body widget, in case data has changed"""
        self.body = self.generate_body()

    def generate_menu_item(self, caption, callback) -> urwid.AttrMap:
        """Generate one button. Subclass to override."""
        button = urwid.Button(caption, on_press=callback)
        return urwid.AttrMap(button, None, focus_map="reversed")

    def keypress(self, size, key):
        if key in self.choices:
            self.choices[key][1](self, focused=self.focus)
            return
        if key in self.internal_choices:
            self.internal_choices[key](focused=self.focus)
            return
        return super().keypress(size, key)

    def move_up(self, focused):
        self.set_focus(max(0, self.focus_position - 1))

    def move_down(self, focused):
        self.set_focus(min(self.focus_position + 1, len(self) - 1))


class MainMenu(Menu):
    def __init__(self, choices):
        super().__init__(choices=choices)

    def generate_menu_item(self, caption, callback) -> urwid.AttrMap:
        """Generate a simpler "button"."""
        button = DecorationButton(caption, on_press=callback,
                                  left="", right="")
        return urwid.AttrMap(button, None, focus_map="reversed")


class StoryBox(urwid.Scrollable):
    """The box that handles the story itself."""

    def __init__(self, game, choices):
        self.internal_choices = {
            'j': ('Move selection one down', self.move_selection_down),
            'k': ('Move selection one up', self.move_selection_up),
            'home': ('Move selection to start', lambda: self.set_selection(0)),
            'end': ('Move selection to last', lambda: self.set_selection(-1)),
            '?': ('Show help', self.open_help_popup),
        }
        self.game = game
        self.choices = choices
        self.selected_part = -1

        # Store the previous size, to be able to adjust scrollpos to the
        # selected text:
        self._cached_size = None

        self.content = ShowPopup(urwid.Pile([]), title="Available keys")
        super().__init__(widget=self.content)
        self.set_selection(-1)

    def keypress(self, size: 'tuple[int, int]',
                 key: 'str') -> 'str | None':
        logger.debug(f"In StoryBox keypress, with key: {key!r}")
        if key in self.choices:
            self.choices[key][1](self)
            return
        if key in self.internal_choices:
            self.internal_choices[key][1]()
            return
        logger.debug(f"In StoryBox: Unhandled key: {key!r}")
        return super().keypress(size, key)

    def render(self, size, focus=False):
        self._cached_size = size
        return super().render(size, focus)

    def move_selection_up(self):
        old_id = self.selected_part
        self.selected_part -= 1
        if self.selected_part < 0:
            self.selected_part = 0

        if old_id != self.selected_part:
            newpos = self.load_text()
            self.set_scrollpos(newpos)

    def move_selection_down(self):
        old_id = self.selected_part
        self.selected_part += 1
        if self.selected_part >= len(self.game.lines):
            self.selected_part = len(self.game.lines) - 1

        if old_id != self.selected_part:
            newpos = self.load_text()
            self.set_scrollpos(newpos)

    def set_selection(self, lineid):
        """Set the selection to a certain part"""
        if lineid > len(self.game.lines) or lineid <= -1:
            lineid = len(self.game.lines) - 1

        old_id = self.selected_part
        self.selected_part = lineid
        if old_id != lineid:
            newpos = self.load_text()
            if lineid == len(self.game.lines) - 1:
                self.set_scrollpos(-1)
            elif lineid == 0:
                self.set_scrollpos(0)
            else:
                self.set_scrollpos(newpos)

    def _get_story_widgets(self, width):
        """Return the story as a list of widgets.

        @param width:
            The width, or number of columns. Related to be able to return the
            correct row number.

        @rtype: tuple
        @return:
            First element is the list of widgets. The second is what row the
            selected part of the story begins at.
        """
        widgets = []
        story = tu.Story(self.game.lines, self.selected_part)
        elements, first_selected = story.convert_to_urwid()
        first_select_row = 0
        # print(f"Start at {first_select_row}, and first element is
        # {first_selected}")
        for i, element in enumerate(elements):
            t = urwid.Text(element)
            # print(f"{i} - Got text {t}")
            if i < (first_selected - 1):
                first_select_row += len(textwrap.wrap(t.text or ".",
                                                      width=width))
                # print(f"{i} - now up to {first_select_row}")
            widgets.append(t)
        # print(f"Ending at {first_select_row}")
        return widgets, first_select_row

    def load_text(self):
        """Load in the games story"""
        width = 70
        if self._cached_size:
            width, _ = self._cached_size
        widgets, first_selected_row = self._get_story_widgets(width)
        self.content.original_widget = urwid.Pile(widgets)
        return first_selected_row

    def open_help_popup(self):
        """View a popup with the key shortcuts"""
        values = []
        for key, data in self.choices.items():
            values.append(f"{key:10} - {data[0]}")
        for key, data in self.internal_choices.items():
            values.append(f"{key:10} - {data[0]}")

        self.content.set_popup_content(urwid.Pile([urwid.Text(v) for v in
                                                   sorted(values)]))
        self.content.open_pop_up()


class DecorationButton(urwid.Button):
    """Override Button to be able to remove the < and > marks."""

    def __init__(self, label, left="", right="", *args, **kwargs):
        self.button_left = self.convert_to_widget(left)
        self.button_right = self.convert_to_widget(right)
        super().__init__(label, *args, **kwargs)

    def convert_to_widget(self, data):
        """Make sure the given data is a widget, or else it becomes a widget"""
        if isinstance(data, str):
            return urwid.Text(data)
        return data


class GameLister(Menu):
    """The list of existing stories to load or manage"""

    def __init__(self, choices, games):
        self.games = games
        super().__init__(choices=choices)

    def generate_body(self):
        gamelist = []
        for game in self.games:
            button = DecorationButton(game['title'], on_press=game['callback'],
                                      user_data=game, left="", right="")
            button.gamedata = game
            gamelist.append(urwid.AttrMap(button, None, focus_map="reversed"))
        return gamelist


class InputWindow(urwid.PopUpLauncher):
    """For popping up a window, asking for user input, with canceling.

    Subclass for different input fields.

    """

    text_width = 70

    def __init__(self, original_widget, question, callback, edit_text=""):
        super().__init__(original_widget)
        self.question = question
        self.edit_text = edit_text
        self.callback = callback

        # TODO: try to implement this without buttons first
        # self.confirm_button = urwid.Button(
        #     "Ok", on_press=lambda _: self.close_pop_up())
        self.set_popup_content()

    def set_popup_content(self):
        """Set or change the content of the popup."""
        edit = ReadlineIshEdit(
            caption=self.question + "\n",
            edit_text=self.edit_text,
            multiline=True,
            allow_tab=False,
        )
        urwid.connect_signal(edit, "change", self.on_edit_change)
        self.popup = urwid.LineBox(urwid.Padding(edit, align="center",
                                                 width=self.text_width))

    def on_edit_change(self, widget, new_text):
        logger.debug(f"Got {new_text!r}")
        if new_text.endswith("\n"):
            self.close_pop_up()
            self.callback(widget, new_text)

    def create_pop_up(self):
        return self.popup

    def get_pop_up_parameters(self):
        # TODO: fix this, crashes at the wrong sizes!
        width, height = self.popup.pack()
        logger.debug(f"got width {width} and height {height}")
        return {'left': 20,
                'top': 2,
                'overlay_width': 'pack',
                'overlay_height': 'pack',
                }

    def keypress(self, size, key):
        # TODO: This does not work. It should probably be in the widget above
        logger.debug("In popuplaunhers' keypress!")
        if key == "ctrl d":
            self.close_pop_up()
            return
        return super().keypress(size, key)


class ReadlineIshEdit(urwid.Edit):
    """Add *some* readline features to the Edit widget.

    Inspired by `urwid_readline`- https://github.com/rr-/urwid_readline/ - but
    disagree with some details, e.g. ctrl+l clearing the whole shebang.

    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Copied from https://github.com/rr-/urwid_readline/:
        word_chars = string.ascii_letters + string.digits + "_",
        self._word_regex1 = re.compile(
            "([%s]+)" % "|".join(re.escape(ch) for ch in word_chars)
        )
        self.keymap = {
            "ctrl w":   self.backward_kill_word,
        }

    def keypress(self, size, key):
        """Subclass to handle extra shortcut keys"""
        if key in self.keymap:
            self.keymap[key]()
            return
        return super().keypress(size, key)

    def backward_word(self):
        """Move the cursor backwards one word"""
        for match in self._word_regex1.finditer(
            self._edit_text[0:self._edit_pos][::-1]
        ):
            self.set_edit_pos(self._edit_pos - match.end(1))
            return
        self.set_edit_pos(0)

    def backward_kill_word(self):
        """Delete the word previous to the cursor"""
        pos = self._edit_pos
        self.backward_word()
        self.set_edit_text(
            self._edit_text[:self._edit_pos] + self._edit_text[pos:]
        )


class ShowPopup(urwid.PopUpLauncher):
    """A simple popup to show some text and quit"""

    def __init__(self, original_widget, title=None, popup_content=None):
        super().__init__(original_widget)
        self.title = title
        self.confirm_button = urwid.Button(
            "Ok", on_press=lambda _: self.close_pop_up())
        if popup_content:
            self.set_popup_content(popup_content)
        else:
            self.popup = urwid.LineBox(self.confirm_button, title=self.title)

    def set_popup_content(self, widget):
        """Set or change the content of the popup.

        The LineBox and ok Button is always included.

        """
        self.popup = urwid.LineBox(urwid.Pile([widget, urwid.Divider(),
                                               self.confirm_button]),
                                   title=self.title)

    def create_pop_up(self):
        return self.popup

    def get_pop_up_parameters(self):
        # TODO: fix this, crashes at the wrong sizes!
        width, height = self.popup.pack()
        logger.debug(f"got width {width} and height {height}")
        return {'left': 2, 'top': 2,
                'overlay_width': 'pack',
                'overlay_height': 'pack',
                }


class ConfirmPopupLauncher(urwid.PopUpLauncher):
    """A confirmation popup"""

    def __init__(self, original_widget, question, callback, user_data):
        super().__init__(original_widget)

        def confirmer(widget):
            logger.debug(f"Confirmed delete: {widget}")
            self.close_pop_up()
            callback(self, user_data)

        confirm_button = urwid.Button("Confirm", on_press=confirmer)

        self.popup = urwid.LineBox(
            urwid.Pile([
                urwid.Text(question),
                urwid.Divider(),
                confirm_button,
                urwid.Button("Cancel", on_press=lambda _: self.close_pop_up()),
            ])
        )

    def create_pop_up(self):
        return self.popup

    def get_pop_up_parameters(self):
        width, height = self.popup.pack()
        return {'left': 2, 'top': 2,
                'overlay_width': width,
                'overlay_height': height}


class Flame(urwid.Text):
    """A simple ASCII flame which can change"""

    def __init__(self):
        super().__init__(self.get_flame())

    def get_flame(self):
        """Get a random flame"""
        return ("flame", "\n".join(random.choice(self.flames)))

    def regenerate_flame(self):
        self.set_text(self.get_flame())

    flames = (
        (
            r"   )   ",
            r"  ) \  ",
            r" / ) ( ",
            r" \(_)/ ",
        ),
        (
            r"   (   ",
            r"  / (  ",
            r" ( / \ ",
            r" \(.)/ ",
        ),
        (
            r"  (    ",
            r"  )\   ",
            r" (\ \  ",
            r" \(.)  ",
        ),
        (
            r"       ",
            r"   /\  ",
            r"  (  \ ",
            r"  \.)/ ",
        ),
        (
            r"    )  ",
            r"   /(  ",
            r"  (\ \ ",
            r"  (.)/ ",
        ),
        (
            r"  /\   ",
            r" ( ^\  ",
            r" |/ \( ",
            r" \(-)/ ",
        ),
        (
            r"  /^\  ",
            r" ( _ ) ",
            r" (/ \( ",
            r" \(-)/ ",
        ),
        (
            r"   ^   ",
            r"  / \  ",
            r" ( \ ) ",
            r" \(-)/ ",
        ),
    )
