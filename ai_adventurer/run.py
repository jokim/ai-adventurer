#!/usr/bin/env python

import logging
import time

import cli_gui


class Game(object):
    """The controller of the game"""

    def __init__(self):
        # The state of where you are in the GUI. A bit too simple, probably.
        self.status = None
        self.gui = cli_gui.GUI()


    def run(self):
        choices = {
            'n': ('New game', self.start_new_game),
            'q': ('Quit', self.quit),
        }

        with self.gui.fullscreen():
            self.gui.show_splashscreen()
            choice = self.gui.start_mainmenu(choices)

            print("chose: " + choice)
            # Call function for next step. Might there be a better way to do this?
            choices[choice][1]()


    def start_new_game(self):
        print("New game!")
        choices = {
            'j': ("Up", self.shift_focus_up),
            'k': ("Down", self.shift_focus_down),
            'r': ("Retry", self.retry),
            'e': ("Edit", self.edit_line),
            'KEY_ENTER': ('Next', self.next_line),
        }

        # TODO: Get an initial line?

        self.gui.start_gameroom(choices=choices, lines=[])


    def next_line(self):
        pass

    def shift_focus_up(self):
        pass

    def shift_focus_down(self):
        pass

    def retry(self):
        pass

    def edit_line(self):
        pass

    def quit(self):
        print("Quitter...")


def main():
    logging.debug("Starting game")
    game = Game()
    game.run()
    logging.debug("Stopping game")


if __name__ == '__main__':
    main()
