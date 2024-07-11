#!/usr/bin/env python

import logging
import time

import cli_gui
import nlp


class Game(object):
    """The controller of the game"""

    def __init__(self):
        # The state of where you are in the GUI. A bit too simple, probably.
        self.status = None
        self.gui = cli_gui.GUI()
        self.nlp = nlp.NLP()

        self.lines = []

        self.game_actions = {
            'j': ("Up", self.shift_focus_up),
            'k': ("Down", self.shift_focus_down),
            'r': ("Retry", self.retry),
            'e': ("Edit", self.edit_line),
            'q': ("Quit", self.quit_game),
            'KEY_ENTER': ('Next', self.next_line),
        }


    def run(self):
        with self.gui.fullscreen():
            self.gui.show_splashscreen()
            self.start_mainmenu_loop()


    def start_mainmenu_loop(self):
        choices = {
            'n': ('New game', self.start_new_game),
            'q': ('Quit', self.quit),
        }
        while True:
            choice = self.gui.print_mainmenu(choices)
            inp = self.gui.get_keyinput()
            if inp in choices:
                choices[inp][1]()

                # TODO: hack for exiting the loop and quitting
                if inp == 'q':
                    return
            elif inp.name in choices:
                choices[inp.name][1]()
            else:
                print("You chose badly (invalid): " + inp)


    def start_new_game(self):
        self.lines = []
        print("New game!")

        self.gui.start_gameroom(choices=self.game_actions, lines=[],
                                status="New game, generating...")

        # TODO: put text generation into its own thread?

        initial_text = self.nlp.generate()
        self.lines.append(initial_text)

        # Avoid duplicating all the text... Have its own object for it?
        self.gui._lines = self.lines
        self.gui.print_screen(status="New game started")

        self.start_game_input_loop()


    def start_game_input_loop(self):
        while True:
            inp = self.gui.get_keyinput()
            if inp in self.game_actions:
                self.game_actions[inp][1]()

                # TODO: hack for ending game and getting back to main menu
                if inp == 'q':
                    return

            elif inp.name in self.game_actions:
                self.game_actions[inp.name][1]()
            else:
                self.gui.send_message("Invalid command")


    def next_line(self):
        """Generate new text"""
        self.gui.send_message("Generate more text...")
        text = self.nlp.generate(self.lines)
        self.lines.append(text)
        self.gui._lines = self.lines
        self.gui.print_screen("New text generated")


    def shift_focus_up(self):
        pass

    def shift_focus_down(self):
        pass

    def retry(self):
        """Retry last generation"""
        self.gui.send_message("Retry last text")
        text = self.nlp.generate(self.lines[:-1])
        self.lines[-1] = text
        self.gui._lines = self.lines
        self.gui.print_screen("New text generated")


    def edit_line(self):
        pass


    def quit_game(self):
        self.gui.send_message("Ending the game - save func missing")
        pass
        # TODO: go to main menu


    def quit(self):
        print("Quitter...")


def main():
    logging.debug("Starting game")
    game = Game()
    game.run()
    logging.debug("Stopping game")


if __name__ == '__main__':
    main()
