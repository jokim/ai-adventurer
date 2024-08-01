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

    def get_keyinput(self):
        """Shortcut for waiting for user key input."""
        with self.term.cbreak(), self.term.hidden_cursor():
            return self.term.inkey()

    def edit_line(self, old_text):
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

    def get_line_input(self, question="Add a new line: "):
        """Ask the user to write a line."""
        print(
            self.term.move_xy(0, self.term.height - 2) + self.term.clear_eol,
            end="",
        )
        newline = input(question).strip()
        return newline

    def get_input_menu(self, choices, title=None):
        """Ask the user to chose an option, and return that.

        The choice format: keys are the character to push for its choice, and
        the values are tuples, where the first must be a human readable name.
        The rest is ignored by this method. Example:

            'n': ('New game', ...),

        """
        status = None
        while True:
            self.print_menu(choices, title=title, status=status)
            inp = self.get_keyinput()
            if inp in choices:
                return choices[inp]
            elif inp.name in choices:
                # This is for characters like 'ENTER_KEY'
                return choices[inp.name]
            else:
                status = f"You chose badly: {inp!r}"

    def print_menu(self, choices, title=None, status=None):
        """Print a menu with the given choices."""
        self.print_header(title=title)

        for key, options in choices.items():
            if key == "KEY_ENTER":
                key = "Enter"
            print(self.term.bold(str(key)) + " - " + options[0])
        print()
        if status:
            print()
            print(status)
        # TODO: Any footer to print?

    def start_gameroom(self, choices, game, status=""):
        """Show the initial GUI for when in a game"""
        self._choices = choices
        self._game = game
        self.print_screen(status=status)

    def send_message(self, message):
        """Send a message to the status field on the screen"""
        print(self.term.move_xy(1, self.term.height - 3), end="")
        print(
            self.term.ljust(message, width=self.term.width - 1, fillchar=" "),
            end="",
        )

    def print_header(self, title=None):
        """Clears the screen and adds the header line"""
        if not title:
            title = "AI adventurer"
        print(self.term.home + self.term.on_black + self.term.clear, end="")
        print(self.term.center(self.term.green_bold(title)))
        print(self.term.darkgrey("\u2500" * self.term.width))

    def print_screen(self, status=""):
        """Print the game screen, with all details."""
        # Note: Smaller screens haven't been tested or adjusted for yet
        self.print_header()
        self.print_content(self._game.lines, self._game.focus)

        # Footer
        print(self.term.move_xy(0, self.term.height - 4), end="")
        # status line
        print(self.term.darkgrey("\u2500" * self.term.width))
        print(" " + status)
        print(self.term.darkgrey("\u2500" * self.term.width))
        submenu = []
        for key, data in self._choices.items():
            submenu.append(
                f"[{self.term.bold}{key}{self.term.normal}] " + f"{data[0]}"
            )

        print(" " + " ".join(submenu), end="")

    def print_content(self, lines, focus):
        """Fill the main content area with the last lines"""
        y_min = 2
        y_max = self.term.height - 5
        y_pos = y_max

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
            print(self.term.gray("No content yet..."))
            return
        while line_nr >= 0:
            line = lines[line_nr]
            rows = self.term.wrap(line, width=min(self.term.width - 10, 120))
            # Make sure blank rows are included
            if not rows:
                rows.append("")
            for row in reversed(rows):
                if line_nr == focus:
                    print(self.term.standout, end="")
                print("%3d   " % line_nr, end="")
                print(row, end="")
                print(self.term.normal, end="")

                y_pos -= 1
                if y_pos <= y_min:
                    return
                print(self.term.move_xy(0, y_pos), end="")

            line_nr -= 1

        # TODO: add an indicator, viewing that you are not at the bottom


class TableEditor(object):
    """Manages the view of a table with data, and input to manipulate it.

    This is an attempt to try to generalise the flow a bit more. Probably a
    prettier solution than this, but the thought behind this, per now:

    - add_action is called to add menu options, and a callable
    - if the given option is selected, the callable is called, and given the
      active row in the table
    - If the callable returns a string, it is presented to the user as a
      message

    Some special options are internal for this class, i.e. moving up and down
    in the table, and exiting the table view.

    """

    def __init__(self, gui, table_data, choices):
        self.data = table_data
        self.gui = gui
        self.focus = 0
        # TODO: change to something better than this!
        self.format = ('%5d ', '%-60s ', '%6s',)
        self.choices = choices

    def add_action(self, key, name, func):
        self.choices[key] = (name, func)

    def activate(self, message=None):
        # TODO: what to do if the list is empty? Gives traceback
        while True:
            self.print_screen(message=message)
            message = None
            key = self.gui.get_keyinput()
            if key == 'q':
                raise UserQuitting()
            elif key == 'j':
                self.shift_focus_down()
                continue
            elif key == 'k':
                self.shift_focus_up()
                continue
            elif key in self.choices:
                return self.choices[key], self.data[self.focus]
                # message = self.choices[key][1](self.data[self.focus])
            elif key.name in self.choices:
                return self.choices[key.name], self.data[self.focus]
                # message = self.choices[key.name][1](self.data[self.focus])
            else:
                message = f"Unknown choice: {key!r}"

    def print_screen(self, message=None):
        self.gui.print_header()
        # TODO: change to move up and down according in respect of self.focus
        for i, line in enumerate(self.data):
            if i == self.focus:
                print(self.gui.term.standout, end="")

            for i, element in enumerate(line):
                formatter = self.format[i]
                print(formatter % (element,), end='')
            print(self.gui.term.normal)
        self.print_footer_menu(message=message)

    def print_footer_menu(self, message=None):
        print(self.gui.term.move_xy(0, self.gui.term.height - 3), end="")
        print(self.gui.term.darkgrey("\u2500" * self.gui.term.width))
        print(message or '')

        choices = self.choices.copy()
        choices['j'] = ('Down', None)
        choices['k'] = ('Up', None)
        choices['q'] = ('Quit', None)
        submenu = []
        for key, data in choices.items():
            if key == "KEY_ENTER":
                key = "Enter"
            submenu.append(
                f"[{self.gui.term.bold}{key}{self.gui.term.normal}] " +
                f"{data[0]}"
            )
        print(" ".join(submenu), end="")

    def shift_focus_down(self):
        # The list starts at 0 at the top, so we increase
        self.focus += 1
        # Don't pass the last line
        if self.focus > len(self.data) - 1:
            self.focus = len(self.data) - 1

    def shift_focus_up(self):
        # The list starts at 0 at the top, so we decrease
        self.focus -= 1
        if self.focus < 0:
            self.focus = 0
