#!/usr/bin/env python

import argparse
import logging
import time

import cli_gui
import nlp


logger = logging.getLogger(__name__)


class Game(object):
    """The controller of the game"""

    def __init__(self):
        # The state of where you are in the GUI. A bit too simple, probably.
        self.status = None
        self.gui = cli_gui.GUI()

        self.lines = []

        self.game_actions = {
            'j': ("Down", self.shift_focus_down),
            'k': ("Up", self.shift_focus_up),
            'r': ("Retry", self.retry),
            'e': ("Edit", self.edit_line),
            'q': ("Quit", self.quit_game),
            'KEY_ENTER': ('Next', self.next_line),
        }


    def run(self):
        with self.gui.activate():
            self.gui.show_splashscreen()
            self.start_mainmenu_loop()


    def start_mainmenu_loop(self):
        # TODO: HACK FOR JUST STARTING A NEW GAME WHILE CODING
        self.start_new_game()
        # TODO: HACK FOR JUST STARTING A NEW GAME WHILE CODING
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
        #self.nlp_thread = nlp.OpenAINLPThread()
        #self.nlp_thread = nlp.LocalNLPThread()
        self.nlp_thread = nlp.GeminiNLPThread()
        #self.nlp_thread = nlp.MockNLPThread()
        print("New game!")

        self.gui.start_gameroom(choices=self.game_actions, lines=[],
                                status="New game, generating...")

        # TODO: These should be per game later
        instructions = """
            You are a very good story writer assistant, helping with creating
            an adventure by the given instructions. Return one sentence,
            continuing the given story.
            """
        # TODO: Temp start, just to have something
        story_line = """
            This is a cyberpunk story, in the year 2345. You are called Lou,
            and are an android, living in the metropoly of New Zhu.
            One day you woke up, and started thinking

            """

        self.lines.append(story_line)
        initial_text = self.nlp_thread.prompt(instructions + "\n\n" + story_line)
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
        self.gui.send_message("Generating more text...")
        text = self.nlp_thread.prompt("Give another sentence", role='system')
        self.lines.append(text)
        self.gui._lines = self.lines
        self.gui.print_screen("New text generated")


    def shift_focus_up(self):
        self.gui.set_focus_up()
        self.gui.print_screen()

    def shift_focus_down(self):
        self.gui.set_focus_down()
        self.gui.print_screen()

    def retry(self):
        """Retry last generation"""
        self.gui.send_message("Retry last text")
        # TODO: remove last line
        text = self.nlp_thread.prompt('', role='system')
        self.lines[-1] = text
        self.gui._lines = self.lines
        self.gui.print_screen("New text generated")


    def edit_line(self):
        """Edit last line/response"""
        newline = self.gui.edit_last_line()
        self.lines[-1] = newline
        self.gui._lines = self.lines
        self.gui.print_screen('Last line updated')


    def quit_game(self):
        self.gui.send_message("Ending the game - save func missing")
        pass
        # TODO: go to main menu


    def quit(self):
        print("Quitter...")


def main():
    parser = argparse.ArgumentParser(
        description='Run the AI adventurer game in the terminal'
    )
    parser.add_argument('-d', '--debug', action='store_true',
                        help='Log debug data to file, for development')
    args = parser.parse_args()

    if args.debug:
        logging.basicConfig(filename='logger.log', encoding='utf-8',
                            level=logging.DEBUG)
    else:
        logging.basicConfig(filename='logger.log', encoding='utf-8',
                            level=logging.WARNING)

    logger.debug("Starting game")
    game = Game()
    game.run()
    logger.debug("Stopping game")


if __name__ == '__main__':
    main()
