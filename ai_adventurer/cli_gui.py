#!/usr/bin/env python
""" The games GUI functionality.

Making use of `blessed` to have a more fancy CLI.

"""

import logging
import subprocess
import tempfile

from blessed import Terminal

logger = logging.getLogger(__name__)


class UserQuitting(Exception):
    """Signalling the user quitting e.g. a menu"""

    pass


class GUI(object):
    """The main GUI of the game.

    Supposed to be the main part the *controller* controls the GUI
    through.

    """

    def __init__(self):
        self.term = Terminal()

    def activate(self):
        """Activate fullscreen mode of the terminal"""
        return self.term.fullscreen()

    def start_input_key(self):
        """Shortcut for waiting for user key input."""
        with self.term.cbreak(), self.term.hidden_cursor():
            return self.term.inkey()

    def start_input_line(self, question="Add a new line: "):
        """Ask the user to write a line."""
        print(
            self.term.move_xy(0, self.term.height - 2) + self.term.clear_eol,
            end="",
        )
        newline = input(question).strip()
        return newline

    def start_input_edit_text(self, old_text):
        """Ask user to edit given text and return the new one."""
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

        return new_text

    def start_input_menu(self, choices, title=None, endkey="q"):
        """Ask the user to chose an option, and return that.

        The choice format: keys are the character to push for its choice, and
        the values are tuples, where the first must be a human readable name.
        The rest is ignored by this method. Example:

            'n': ('New game', ...),

        The quit option (`endkey`) handled specially, raising UserQuitting.

        """
        status = None
        new_choices = choices.copy()
        new_choices[endkey] = ("Quit", None)
        while True:
            self.print_menu(new_choices, title=title, status=status)
            inp = self.start_input_key()
            if inp in choices:
                return choices[inp]
            elif inp.name in choices:
                # This is for characters like 'ENTER_KEY'
                return choices[inp.name]
            elif inp == endkey:
                raise UserQuitting()
            else:
                status = f"You chose badly: {inp!r}"

    def print_menu(self, choices, title=None, status=None):
        """Print a menu with the given choices."""
        self._print_header(title=title)

        for key, options in choices.items():
            if key == "KEY_ENTER":
                key = "Enter"
            print(self.term.bold(str(key)) + " - " + options[0])
        print()
        if status:
            print()
            print(status)
        # TODO: Any footer to print?

    def send_message(self, message):
        # TODO: move this to GameWindow somehow
        """Send a message to the status field on the screen"""
        print(self.term.move_xy(1, self.term.height - 3), end="")
        print(
            self.term.ljust(message, width=self.term.width - 1, fillchar=" "),
            end="",
        )


class Window(object):
    """Managing the terminal as a windows with something.

    Subclasses handles more specific types of data/text.

    Thought behind the flow:

    - Initiate object with proper data and users choices
    - .activate() prints and waits for user input
    - Special input, like moving up or down, is handled by the object
    - The users choice is returned. This means the controller needs to loop
      over `.activate()` if you expect the user to do more in the window

    """

    game_title = "AI adventurer"

    def __init__(self, gui, choices, endkey="q"):
        self.gui = gui
        self.term = gui.term
        self.choices = choices
        self.endkey = endkey
        self.internal_choices = {endkey: ("Quit", None)}

    def activate(self, message=None):
        pass

    def _print_header(self, title=None):
        """Clears the screen and adds the header line"""
        if title:
            title = f"{title} - {self.game_title}"
        else:
            title = self.game_title
        print(self.term.home + self.term.on_black + self.term.clear, end="")
        print(self.term.black_on_darkorange_bold(
              self.term.ljust(self.term.black_on_darkorange_bold(title))))
        # TODO: cut the title at length of line

    def _get_footer_content(self, message=None):
        ret = []
        ret.append(self.term.move_xy(0, self.term.height - 2))
        ret.append(self.term.black_on_darkorange)
        ret.append(self.term.ljust(message or ""))
        ret.append("\n")

        choices = self.choices.copy()
        choices.update(self.internal_choices)

        submenu = []
        for key, data in choices.items():
            if key == "KEY_ENTER":
                key = "Enter"
            submenu.append(
                self.term.darkgray_on_darkorange("[")
                + self.term.black_on_darkorange_bold(key)
                + self.term.darkgray_on_darkorange("]")
                + self.term.black_on_darkorange(data[0])
            )
        ret.append(self.term.black_on_darkorange(self.term.ljust(
            self.term.black_on_darkorange(" ").join(submenu),
            width=self.term.width)))
        retout = "".join(ret)
        return retout

    def _print_footer_menu(self, message=None):
        print(self._get_footer_content(message=message), end="")


class MenuWindow(Window):
    """Simple menu window"""

    def activate(self, message=None):
        super().activate(message=message)
        while True:
            self._print_screen(message=message)
            inp = self.gui.start_input_key()
            if inp in self.choices:
                return self.choices[inp]
            elif inp.name in self.choices:
                # This is for characters like 'ENTER_KEY'
                return self.choices[inp.name]
            elif inp == self.endkey:
                raise UserQuitting()
            else:
                message = f"You chose badly: {inp!r}"

    def _print_screen(self, message=None):  # title=None TODO
        """Print a menu with the given choices."""
        self._print_header()

        choices = self.choices.copy()
        choices.update(self.internal_choices)

        y_pos = 1
        y_max = self.term.height - 3

        for key, options in choices.items():
            if key == "KEY_ENTER":
                key = "Enter"
            print(self.term.ljust(self.term.bold(str(key)) + " - " +
                                  options[0], width=self.term.width))
            y_pos += 1
        if message:
            print()
            print(message)
            y_pos += 2
        while y_pos < y_max:
            print(self.term.ljust(" ", width=self.term.width))
            y_pos += 1


class EditorWindow(Window):
    """Handles data with more editor functionality"""

    def __init__(self, gui, choices, data):
        super().__init__(gui, choices)
        self.data = data
        self.focus = 0
        self.internal_choices.update(
            {
                "j": ("Down", None),
                "k": ("Up", None),
            }
        )

    def activate(self, message=None):
        while True:
            self._print_screen(message=message)
            message = None
            key = self.gui.start_input_key()
            if key == "q":
                raise UserQuitting()
            elif key == "j":
                self.shift_focus_down()
                continue
            elif key.name == "KEY_RIGHT":
                self.shift_focus_down(10)
                continue
            elif key.name == "KEY_DOWN":
                self.shift_focus_down()
                continue
            elif key.name == "KEY_PGDOWN":
                self.shift_focus_down(10)
                continue
            elif key == "k":
                self.shift_focus_up()
                continue
            elif key.name == "KEY_UP":
                self.shift_focus_up()
                continue
            elif key.name == "KEY_LEFT":
                self.shift_focus_up(10)
                continue
            elif key.name == "KEY_PGUP":
                self.shift_focus_up(10)
                continue
            elif key.name == "KEY_HOME":
                self.set_focus(0)
                continue
            elif key.name == "KEY_END":
                self.set_focus(-1)
                continue
            elif key in self.choices:
                return (
                    self.choices[key],
                    self.focus,
                    self._get_element(self.focus),
                )
            elif key.name in self.choices:
                return (
                    self.choices[key.name],
                    self.focus,
                    self._get_element(self.focus),
                )
            else:
                message = f"Unknown choice: {key!r}"

    def _get_elements(self):
        """Get the data that the user could manage. Subclass!"""
        return self.data

    def _get_element(self, elementid):
        if not self.data:
            return None
        return self.data[elementid]

    def shift_focus_down(self, jumps=1):
        # The list starts at 0 at the top, so we increase
        self.focus += jumps
        # Don't pass the last line
        if self.focus > len(self._get_elements()) - 1:
            self.focus = len(self._get_elements()) - 1

    def shift_focus_up(self, jumps=1):
        # The list starts at 0 at the top, so we decrease
        self.focus -= jumps
        if self.focus < 0:
            self.focus = 0

    def set_focus(self, elementid):
        assert isinstance(elementid, int) and elementid >= -1
        if elementid == -1:
            self.focus = len(self._get_elements()) - 1
        else:
            self.focus = elementid


class TableEditWindow(EditorWindow):
    """View a simple table with data the user has _simple_ actions on.

    table_data must be a list with lists. Each element is a row, and the
    internal items gets into columns.

    """

    def __init__(self, gui, choices, data):
        super().__init__(gui=gui, choices=choices, data=data)
        # TODO: change to something better than this!
        self.format = (
            "%5d ",
            "%-60s ",
            "%6s",
        )

    def _print_screen(self, message=None):
        self._print_header()
        # TODO: change to move up and down according in respect of self.focus
        for i, line in enumerate(self.data):
            if i == self.focus:
                print(self.term.standout, end="")
            for i, element in enumerate(line):
                formatter = self.format[i]
                print(formatter % (element,), end="")
            print(self.term.normal)
        self._print_footer_menu(message=message)


class GameWindow(EditorWindow):

    text_width = 120

    def __init__(self, gui, choices, game):
        super().__init__(gui=gui, choices=choices, data=game)

    def _print_screen(self, message=""):
        """Print the game screen, with all details."""
        self._print_header(title=self.data.title)
        self._print_gamedata()
        self._print_footer_menu(message=message)
        return

    def _get_elements(self):
        return self.data.lines

    def _get_element(self, elementid):
        if not self.data.lines:
            return None
        return self.data.lines[elementid]

    def _print_gamedata(self):
        """Fill the main content area with the last lines"""
        y_min = 1
        y_max = self.term.height - 3
        y_pos = y_max

        focus = self.focus
        lines = self.data.lines

        # Start at the bottom and work upwards
        print(self.term.move_xy(0, y_pos), end="")

        # Focus defaults to -1, which is the last line
        if focus == -1:
            focus = len(lines) - 1
        # The focus might have moved past the last line
        if focus > len(lines) - 1:
            focus = len(lines) - 1

        # Walk backward, from the bottom, and stop when you reach y_min
        # Let the active line be at the bottom
        line_nr = focus
        # But, if the active line is not the last, show one more:
        if line_nr < len(lines) - 1:
            line_nr = focus + 1

        if len(lines) == 0:
            print(self.term.ljust(self.term.gray("No content yet..."),
                                  width=self.term.width))
            y_pos -= 1
        else:
            while line_nr >= 0:
                line = lines[line_nr]
                rows = self.term.wrap(line, width=min(self.term.width - 10,
                                                      self.text_width))
                # Make sure blank rows are included
                if not rows:
                    rows.append("")
                for row in reversed(rows):
                    if line_nr == focus:
                        print(self.term.standout, end="")
                    print(self.term.ljust(row, width=self.term.width), end="")
                    print(self.term.normal, end="")

                    y_pos -= 1
                    if y_pos < y_min:
                        return
                    print(self.term.move_xy(0, y_pos), end="")

                line_nr -= 1
        while y_pos >= y_min:
            print(self.term.move_xy(0, y_pos)
                  + self.term.ljust(" ", width=self.term.width),
                  end="")
            y_pos -= 1
