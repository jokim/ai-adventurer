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
        input = self._get_keyinput()

        #print("you chose: '" + inp + "'")
        #print("type: '" + str(type(inp)) + "'")
        #print("repr: '" + str(repr(inp)) + "'")
        #time.sleep(2)


    def _get_keyinput(self):
        """Shortcut for waiting for user key input."""
        with self.term.cbreak(), self.term.hidden_cursor():
            return self.term.inkey()

    def start_mainmenu(self, choices):
        """Display a menu, and returns the users choice.

        Invalid choices are retried from the user.

        @param choices: 
            A dict, where the key is the keyboard input for the choice. The
            value is a dict, with first element is an english title for the
            choice. The rest is ignored.

        @return: The users choice, i.e. the chosen key from the dict.

        """
        while True:
            self._print_mainmenu(choices)
            inp = self._get_keyinput()
            if inp in choices:
                return inp
            else:
                print(self.term.red("You chose badly (invalid): " + inp))
                time.sleep(0.4)


    def _print_mainmenu(self, choices):
        print(self.term.home + self.term.on_black + self.term.clear)  
        print(self.term.move_down(2))
        for key, options in choices.items():
            print(self.term.bold(str(key)) + ' - ' + options[0])
        print()
        print("Choose wisely!")


    def start_gameroom(self, choices, lines=[]):
        """Show the initial GUI for when in a game"""
        self._choices = choices
        self.print_screen()

        self._get_keyinput()


    def print_screen(self, status=""):
        """Print the game screen, with all details."""
        # Note: Smaller screens haven't been tested or adjusted for yet

        # Header
        print(self.term.home + self.term.on_black + self.term.clear, end='')
        print(self.term.center(self.term.green_bold("AI adventurer")))
        print(self.term.darkgrey('-' * self.term.width))

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
