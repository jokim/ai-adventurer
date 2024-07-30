#!/usr/bin/env python

import argparse
import configparser
import logging
import re

import cli_gui
import nlp
import db


logger = logging.getLogger(__name__)

default_configfile = "config.ini"
default_secretsfile = "secrets.ini"


default_instructions = """
    # This is the instructions that is given to the AI at each step in the
    # story.
    # - All lines starting with hash (#) are removed before given to the AI.
    # - Leave the instructions blank to reset to the default instructions.

    You are an excellent story writer, writing remarkable fantasy fiction.

    Writing Guidelines: Use first person perspective, and present tense, unless
    the story starts different. Use writing techniques to bring the world and
    characters to life. Use rich imagery lightly, but be specific and to the
    point. Focus on details that makes the story alive. Let the characters
    develop, and bring out their motivations, relationships, thoughts and
    complexity. Keep the story on track, but be creative and allow surprising
    subplots. Include dialog with the characters. Avoid repetition and
    summarisation. Use humor.

    Return one sentence, continuing the given story.

    """


default_details = """
    # Story summary and details.
    #
    # This is where you could put details that are important for the story. For
    # example a summary of how the story should go, or details about certain
    # characters.
    #
    # All lines starting with hash (#) are ignored.

    # The default is quite generic...
    This is a story about you, going on an adventurous journey. You will
    experience a lot of things, and will be surprised from time to time.
    """


def remove_comments(text):
    ret = []
    for line in text.splitlines():
        line = line.lstrip()
        if not line.startswith("#"):
            ret.append(line)
    return "\n".join(ret)


class GameController(object):
    """The controller of the game"""

    def __init__(self, config, secrets):
        self.config = config
        self.secrets = secrets
        self.gui = cli_gui.GUI()
        self.db = db.Database()

        self.game_actions = {
            "j": ("Down", self.shift_focus_down),
            "k": ("Up", self.shift_focus_up),
            "r": ("Retry", self.retry),
            "e": ("Edit", self.edit_active_line),
            "d": ("Del", self.delete_active_line),
            "a": ("Add", self.add_line),
            "t": ("Title", self.edit_title),
            "s": ("Story", self.edit_story_details),
            "i": ("Instruct", self.edit_instructions),
            "q": ("Quit", self.quit_game),
            "KEY_ENTER": ("Next", self.next_line),
        }

    def run(self):
        with self.gui.activate():
            self.start_mainmenu_loop()

    def start_mainmenu_loop(self):
        choices = {
            "n": ("New game", self.start_new_game),
            "l": ("Load game", self.load_game),
            "c": (
                "Write config file (config.ini and secrets.ini)",
                self.edit_config,
            ),
            "q": ("Quit", self.quit),
        }
        while True:
            choice = self.gui.get_input_menu(choices)

            # TODO: hack for exiting the loop and quitting
            if choice == choices["q"]:
                return
            choice[1]()

    def load_game(self):
        choices = {}

        for game in self.db.get_games():
            choices[str(game["gameid"])] = (f"{game['title']}", game["gameid"])
        choices["q"] = ("Quit this menu", None)

        choice = self.gui.get_input_menu(choices, title="Pick a game to load")
        if choice == choices["q"]:
            return
        self.game = Game(
            db=self.db, nlp=self.get_nlp_handler(), gameid=choice[1]
        )

        self.gui.start_gameroom(
            choices=self.game_actions, game=self.game, status="Game loaded"
        )
        self.start_game_input_loop()

    def edit_config(self):
        self.config.write(open(default_configfile, "w"))
        self.secrets.write(open(default_secretsfile, "w"))

    def start_new_game(self):
        self.game = Game(db=self.db, nlp=self.get_nlp_handler())
        title = self.gui.get_line_input("An initial title for the story? ")
        self.game.set_title(title)
        self.game.set_instructions(default_instructions)
        self.game.set_details(default_details)
        self.game.add_lines(self.game.get_introduction())
        self.gui.start_gameroom(
            choices=self.game_actions,
            game=self.game,
            status="Started new game",
        )
        self.start_game_input_loop()

    def start_game_input_loop(self):
        while True:
            inp = self.gui.get_keyinput()
            if inp in self.game_actions:
                self.game_actions[inp][1]()

                # TODO: hack for ending game and getting back to main menu
                if inp == "q":
                    return

            elif inp.name in self.game_actions:
                self.game_actions[inp.name][1]()
            else:
                self.gui.send_message("Invalid command")

    def next_line(self):
        """Generate new text"""
        self.gui.send_message("Generating more text...")
        self.game.generate_next_lines()
        self.gui.print_screen("New text generated")

    def shift_focus_up(self):
        self.game.set_focus_up()
        self.gui.print_screen()

    def shift_focus_down(self):
        self.game.set_focus_down()
        self.gui.print_screen()

    def retry(self):
        """Regenerate chosen line"""
        self.gui.send_message("Retry selected text")
        self.game.retry_active_line()
        self.gui.print_screen("New text generated")

    def edit_active_line(self):
        """Edit chosen line/response"""
        _, oldline = self.game.get_active_line()
        newline = self.gui.edit_line(oldline)
        # TODO: what to do if it gets blank? Just save it?
        self.game.change_active_line(newline)
        self.gui.print_screen("Last line updated")

    def add_line(self):
        """Write a new line/response"""
        newline = self.gui.get_line_input()
        if newline:
            self.game.add_lines(newline)
        self.gui.print_screen()

    def delete_active_line(self):
        """Delete chosen line/response"""
        self.game.delete_active_line()
        self.gui.print_screen("Line deleted")

    def edit_title(self):
        new_title = self.gui.edit_line(self.game.title)
        if new_title:
            self.game.set_title(new_title)
            self.gui.print_screen("Title updated")
        else:
            self.gui.print_screen("Title not updated")

    def edit_instructions(self):
        new_instructions = self.gui.edit_line(self.game.instructions)

        if not remove_comments(new_instructions.strip()).strip():
            new_instructions = default_instructions

        self.game.set_instructions(new_instructions)
        self.gui.print_screen("Instructions updated")

    def edit_story_details(self):
        new_details = self.gui.edit_line(self.game.details)

        if not remove_comments(new_details.strip()).strip():
            new_details = default_details

        self.game.set_details(new_details)
        self.gui.print_screen("Story summary updated")

    def quit_game(self):
        self.gui.send_message("Quit this game")
        self.game.save()

    def quit(self):
        print("Quitter...")

    def get_nlp_handler(self):
        if not hasattr(self, "nlp"):
            model = self.config["DEFAULT"]["nlp_model"]
            extra = None
            if ':' in model:
                model, extra = model.split(':', 1)
            if model in ('local', 'huggingface') and extra is None:
                raise Exception("Missing param for NLP model, after : in conf")
            nlp_class = nlp.get_nlp_class(model)
            self.nlp = nlp_class(secrets=self.secrets, extra=extra)
        return self.nlp


class Game(object):

    def __init__(self, db, nlp, gameid=None):
        self.db = db
        self.nlp = nlp
        self.focus = -1

        if gameid:
            self.gameid = gameid
            db_game = self.db.get_game(gameid)
            self.instructions = db_game["instructions"]
            self.details = db_game["details"]
            self.title = db_game["title"]
            self.lines = self.db.get_lines(gameid)
        else:
            self.lines = []
            self.instructions = ""
            self.details = ""
            self.title = "Test 123"
            self.gameid = db.create_new_game(self.title)

    def save(self):
        self.db.save_game(self)

    @classmethod
    def cleanup_text(cls, text):
        """Remove some unnecessary whitespace"""
        if isinstance(text, (list, tuple)):
            return [cls.cleanup_text(t) for t in text]
        # Replace multiple newlines with at most two (keeping paragraphs)
        text = re.sub(r"\n{3,}", "\n\n", text)
        # Replace multiple spaces with a single space
        text = re.sub(r"[ \t\r\f\v]+", " ", text)
        return text

    def set_instructions(self, text):
        """Set the instructions for the NLP generations."""
        self.instructions = self.cleanup_text(text)
        self.save()

    def set_details(self, text):
        """Set story details and other important information"""
        self.details = self.cleanup_text(text)
        self.save()

    def set_title(self, new_title):
        self.title = self.cleanup_text(new_title).strip()
        self.save()

    def get_active_line(self):
        return (self.focus, self.lines[self.focus])

    def add_lines(self, text):
        """Add text to continue the story."""
        text = self.cleanup_text(text)
        self.lines.append(text)
        # Set focus to the new line. Not sure if that is intuitive?
        self.focus = len(self.lines) - 1
        self.save()

    def _generate_prompt(self, text=None):
        # TODO: Should the instruction go into the NLP object creation, since
        # the APIs have its own parameter for that? Or are there no difference?
        prompt = [remove_comments(self.instructions)]
        details = remove_comments(self.details)
        prompt.append(f"\n---\nThe title of the story: '{self.title}'")
        if details.strip():
            prompt.append("\n---\nImportant details about the story:")
            prompt.append(details)

        prompt.append("\n---\nAnd here is the story so far:")
        prompt.extend(self.lines)
        if text:
            prompt.append(text)

        prompt = self.cleanup_text(prompt)

        # TODO: check if all APIs support lists of just text
        return self.cleanup_text(self.nlp.prompt(prompt))

    def get_introduction(self):
        """Make the AI come up with the initial start of the story."""
        prompt = [remove_comments(self.instructions)]
        details = remove_comments(self.details)
        prompt.append(f"\n---\nThe title of the story: '{self.title}'\n")
        if details.strip():
            prompt.append("\n---\nImportant details about the story:\n")
            prompt.append(details)

        prompt.append("\n---\nGive me three sentences that starts this story.")
        return self.cleanup_text(self.nlp.prompt(prompt))

    def generate_next_lines(self, instructions=None):
        more = self._generate_prompt(instructions)
        self.add_lines(more)
        self.save()
        return more

    def delete_line(self, lineid):
        del self.lines[lineid]
        self.set_focus_up()
        self.save()

    def delete_active_line(self):
        return self.delete_line(self.focus)

    def retry_active_line(self):
        if self.focus is None or self.focus == len(self.lines) - 1:
            # Only support retrying last line for now. Haven't implemented
            # changing inside of the chain yet.
            self.delete_active_line()
            return self.generate_next_lines()
        else:
            print("Can't retry inside, per now")
            logger.warning("Can't retry inside chain, per now")

        self.save()

    def change_active_line(self, new_text):
        self.lines[self.focus] = new_text

    def set_focus_up(self):
        """Move focus up one line.

        "Up" is here upwards in the list, that is counting down to 0. 0 is at
        the top.

        """
        if self.focus == -1:
            # move up to next last
            self.focus = len(self.lines) - 2
        elif self.focus == 0:
            # you are already at the top
            return
        else:
            self.focus -= 1

        # in case of bugs
        if self.focus < -2:
            self.focus = 0

    def set_focus_down(self):
        """Move focus up one line"""
        if self.focus == -1:
            # keep at bottom
            self.focus = len(self.lines) - 1
        else:
            self.focus += 1

        # If trying to pass the last line
        if self.focus > len(self.lines) - 1:
            self.focus = len(self.lines) - 1


def load_config(config_file, args):
    """Using a simple INI file by now"""
    default_settings = {
        "DEFAULT": {
            # See ai_adventurer/nlp.py for available models
            "nlp_model": "gemini-1.5-flash",
        },
    }
    config = configparser.ConfigParser()
    config.read_dict(default_settings)
    config.read(config_file)

    # Override with command-line arguments
    if args.nlp_model:
        config["DEFAULT"]["nlp_model"] = args.nlp_model

    return config


def load_secrets(config_file):
    """I like to have the secrets separated from the rest of the config."""
    default_settings = {
        "DEFAULT": {
            "openai-key": "CHANGEME",
            "gemini-key": "CHANGEME",
        },
    }
    config = configparser.ConfigParser()
    config.read_dict(default_settings)
    config.read(config_file)

    # Not passing any variables as script arguments, since these are secrets.
    return config


def main():
    parser = argparse.ArgumentParser(
        description="Run the AI adventurer game in the terminal"
    )
    parser.add_argument(
        "-d",
        "--debug",
        action="store_true",
        help="Log debug data to file, for development",
    )
    parser.add_argument(
        "--config-file",
        type=str,
        metavar="FILENAME",
        default=default_configfile,
        help="Where the config is located. Default: %(default)s",
    )
    parser.add_argument(
        "--secrets-file",
        type=str,
        metavar="FILENAME",
        default=default_secretsfile,
        help="Where the secrets are located. Default: %(default)s",
    )
    parser.add_argument(
        "--nlp-model",
        type=str,
        metavar="MODEL",
        help="Which AI NLP model to use",
    )
    parser.add_argument(
        "--list-nlp-models",
        action="store_true",
        help="List available AI NLP models",
    )

    args = parser.parse_args()

    if args.debug:
        logging.basicConfig(
            filename="logger.log", encoding="utf-8", level=logging.DEBUG
        )
    else:
        logging.basicConfig(
            filename="logger.log", encoding="utf-8", level=logging.WARNING
        )

    if args.list_nlp_models:
        for m in nlp.models:
            print(m)
        return

    config = load_config(args.config_file, args)
    secrets = load_secrets(args.secrets_file)

    logger.debug("Starting game")
    game = GameController(config, secrets)
    game.run()
    logger.debug("Stopping game")


if __name__ == "__main__":
    main()
