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

        # Call function for next step. Might there be a better way to do this?
        choices[choice][1]()


    def start_new_game(self):
        print("New game!")


    def quit(self):
        print("Quitter...")


def main():
    logging.debug("Starting game")
    game = Game()
    game.run()
    logging.debug("Stopping game")


if __name__ == '__main__':
    main()
