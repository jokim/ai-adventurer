#!/usr/bin/env python
""" The games GUI functionality.

Making use of `blessed` to have a more fancy CLI.

"""

import logging
import time

from blessed import Terminal

logger = logging.getLogger(__name__)

class GUI(object):
    """The main GUI of the game.

    Supposed to be the main part the *controller* controls the GUI
    through.

    """

    def __init__(self):
        self.term = Terminal()


    def activate(self):
        return self.term.fullscreen()


    def show_splashscreen(self):
        print(self.term.home + self.term.on_black + self.term.clear)  
        print(self.term.move_y(self.term.height // 2))
        print(self.term.black_on_darkkhaki(self.term.center('AI storyhelper')))
        print(self.term.move_y(self.term.height // 2))

        # TODO Ascii logo art!

        print(self.term.move_down(2))
        print(self.term.center("Your own adventures, from your imagination"))

        # Press any key...
        #input = self.get_keyinput()

        #print("you chose: '" + inp + "'")
        #print("type: '" + str(type(inp)) + "'")
        #print("repr: '" + str(repr(inp)) + "'")
        #time.sleep(2)


    def get_keyinput(self):
        """Shortcut for waiting for user key input."""
        with self.term.cbreak(), self.term.hidden_cursor():
            return self.term.inkey()


    def edit_line(self, old_text):
        """Ask user to edit given text and return the new one."""
        # TODO: fix this better! Just asking for input now...
        print(self.term.move_xy(0, self.term.height - 2) + self.term.clear_eol, end='')
        newline = input("Change last line to: ").strip()
        return newline


    def get_line_input(self):
        """Ask the user to write a line."""
        print(self.term.move_xy(0, self.term.height - 2) + self.term.clear_eol, end='')
        newline = input("Add a new line: ").strip()
        return newline


    def print_mainmenu(self, choices):
        print(self.term.home + self.term.on_black + self.term.clear)  
        print(self.term.move_down(2))
        for key, options in choices.items():
            print(self.term.bold(str(key)) + ' - ' + options[0])
        print()
        print("Choose wisely!")


    def start_gameroom(self, choices, game, status=''):
        """Show the initial GUI for when in a game"""
        self._choices = choices
        self._game = game
        self.print_screen(status=status)


    def send_message(self, message):
        """Send a message to the status field on the screen"""
        print(self.term.move_xy(1, self.term.height - 3), end='')
        print(self.term.ljust(message, width=self.term.width - 1, fillchar=' '), end='')


    def print_screen(self, status=""):
        """Print the game screen, with all details."""
        # Note: Smaller screens haven't been tested or adjusted for yet

        # Header
        print(self.term.home + self.term.on_black + self.term.clear, end='')
        print(self.term.center(self.term.green_bold("AI adventurer")))
        print(self.term.darkgrey('-' * self.term.width))

        # Main content
        # TODO: Fix all the lines properly, but just print them dumbly for now
        self.print_content(self._game.lines, self._game.focus)

        # Footer
        print(self.term.move_xy(0, self.term.height - 4), end='')
        # status line
        print(self.term.darkgrey('-' * self.term.width))
        print(' ' + status)
        print(self.term.darkgrey('-' * self.term.width))
        submenu = []
        for key, data in self._choices.items():
            submenu.append(f'[{self.term.bold}{key}{self.term.normal}] {data[0]}')

        print(' ' + ' '.join(submenu), end='')


    def print_content(self, lines, focus):
        """Fill the main content area with the last lines"""
        y_min = 2
        y_max = self.term.height - 5
        y_pos = y_max

        # Start at the bottom and work upwards
        print(self.term.move_xy(0, y_pos), end='')

        # Focus defaults to -1, which is the last line
        if focus == -1:
            focus = len(lines) - 1

        i = len(lines) - 1
        while i >= 0:
            line = lines[i]
            rows = self.term.wrap(line, width=min(self.term.width - 10, 120))
            for row in reversed(rows):
                if i == focus:
                    print(self.term.standout, end='')
                print('%3d   ' % i, end='')
                print(row, end='')
                print(self.term.normal, end='')

                y_pos -= 1
                if y_pos <= y_min:
                    return
                print(self.term.move_xy(0, y_pos), end='')

            i -= 1

        # TODO: add an indicator, viewing that you are not at the bottom
