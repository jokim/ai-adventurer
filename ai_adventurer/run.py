#!/usr/bin/env python

import argparse
import logging
import re
import time

import cli_gui
import nlp
import db


logger = logging.getLogger(__name__)


class GameController(object):
    """The controller of the game"""

    def __init__(self):
        # The state of where you are in the GUI. A bit too simple, probably.
        self.status = None
        self.gui = cli_gui.GUI()
        self.db = db.Database()

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
        nlp_thread = nlp.OpenAINLPThread()
        #nlp_thread = nlp.LocalNLPThread()
        #nlp_thread = nlp.GeminiNLPThread()
        #nlp_thread = nlp.MockNLPThread()

        self.game = Game(db=self.db, nlp=nlp_thread)
        print("New game!")

        self.gui.start_gameroom(choices=self.game_actions, lines=[],
                                status="New game, generating...")

        # TODO: These should be per game later
        self.game.set_instructions("""
            You are a very good story writer assistant, helping with creating
            an adventure by the given instructions. Return one sentence,
            continuing the given story.
            """)

        # TODO: Temp start, just to have something
        self.game.add_lines("""
            This is a cyberpunk story, in the year 2345. You are called Lou,
            and are an android, living in the metropoly of New Zhu.
            One day you woke up, and started thinking
            """)

        # Avoid duplicating all the text... Have its own object for it?
        self.gui._lines = self.game.lines
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
        self.game.generate_next_lines()
        self.gui._lines = self.game.lines
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
        self.game.retry_last_line()
        self.gui._lines = self.game.lines
        self.gui.print_screen("New text generated")


    def edit_line(self):
        """Edit last line/response"""
        newline = self.gui.edit_last_line()
        self.game.change_last_line(newline)
        self.gui._lines = self.game.lines
        self.gui.print_screen('Last line updated')


    def quit_game(self):
        self.gui.send_message("Quit this game")
        self.game.save()
        # TODO: go to main menu


    def quit(self):
        print("Quitter...")


class Game(object):

    def __init__(self, db, nlp):
        self.db = db
        self.nlp = nlp
        # TODO: How to manage a separation between the story and instructions?
        self.lines = []
        self.gameid = db.get_next_id()


    def save(self):
        self.db.save_game(self)


    @staticmethod
    def cleanup_text(text):
        """Remove some unncessary whitespace"""
        # Replace multiple newlines with at most two
        text = re.sub(r'\n{3,}', '\n\n', text)
        # Replace multiple spaces with a single space
        text = re.sub(r'\s+', ' ', text)
        return text


    def set_instructions(self, text):
        """Set the instructions for the NLP generations."""
        self.instructions = self.cleanup_text(text)
        self.db.save_game(self)


    def add_lines(self, text):
        """Add text to continue the story."""
        text = self.cleanup_text(text)
        self.lines.append(text)
        self.db.add_lines(self.gameid, text)


    def _generate_prompt(self, text=None):
        # TODO: Should the instruction go into the NLP object creation, since
        # the APIs have its own parameter for that? Or are there no difference?
        prompt = [self.instructions,]
        prompt.extend(self.lines)
        if text:
            prompt.append(text)

        # TODO: check if all APIs support lists of just text
        return self.cleanup_text(self.nlp.prompt(prompt))


    def generate_next_lines(self, instructions=None):
        more = self._generate_prompt(instructions)
        self.add_lines(more)
        return more


    def retry_last_line(self):
        del self.lines[-1]
        return self.generate_next_lines()


    def change_last_line(self, new_text):
        self.lines[-1] = new_text



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
    game = GameController()
    game.run()
    logger.debug("Stopping game")


if __name__ == '__main__':
    main()
