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

        # TODO: Fix setting up fullscreen so that the terminal gets back to its
        # old self when quitting the game. I just have to understand the contex
        # of `with` first...
        #with term.fullscreen():
        #    print(term.home + term.on_black + term.clear)  
        #    gui_splashscreen(term)
        #    gui_startmenu(term)


    # TODO: Isn't in use, but is keept to remember if I do the `with` wrong...
    def _start(self):
        """Start the view in the terminal, and get to main menu."""
        with self.term.fullscreen():
            self.show_splashscreen()
            self.start_mainmenu()


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
        with self.term.cbreak(), self.term.hidden_cursor():
            inp = self.term.inkey()


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
            with self.term.cbreak(), self.term.hidden_cursor():
                inp = self.term.inkey()
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


    # TODO: test key input!
    # Enter key-at-a-time input mode using Terminal.cbreak() or Terminal.raw()
    # context managers, and read timed key presses using Terminal.inkey().
