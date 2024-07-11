#!/usr/bin/env python
""" The games GUI functionality.

Making use of `blessed` to have a more fancy CLI.

"""

import time

from blessed import Terminal


class GUI(object):
    """The main GUI of the game.

    Supposed to be the main part the *controller* controls the GUI
    through.

    """

    def __init__(self):
        self.term = Terminal()


    def fullscreen(self):
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
        input = self.get_keyinput()

        #print("you chose: '" + inp + "'")
        #print("type: '" + str(type(inp)) + "'")
        #print("repr: '" + str(repr(inp)) + "'")
        #time.sleep(2)


    def get_keyinput(self):
        """Shortcut for waiting for user key input."""
        with self.term.cbreak(), self.term.hidden_cursor():
            return self.term.inkey()


    def print_mainmenu(self, choices):
        print(self.term.home + self.term.on_black + self.term.clear)  
        print(self.term.move_down(2))
        for key, options in choices.items():
            print(self.term.bold(str(key)) + ' - ' + options[0])
        print()
        print("Choose wisely!")


    def start_gameroom(self, choices, lines=[], status=''):
        """Show the initial GUI for when in a game"""
        self._choices = choices
        self._lines = lines
        self.print_screen(status=status)


    def send_message(self, message):
        """Send a message to the status field on the screen"""
        print(self.term.move_xy(1, self.term.height - 3), end='')
        #print(self.term.clear, end='')
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
        for line in self._lines:
            for l in self.term.wrap(line):
                # TODO: add focus icon here, later
                print("  " + l)

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
