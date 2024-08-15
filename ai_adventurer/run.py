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


def cleanup_text(text):
    """Remove some unnecessary whitespace"""
    if isinstance(text, (list, tuple)):
        return [cleanup_text(t) for t in text]
    # Replace multiple newlines with at most two (keeping paragraphs)
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Replace multiple spaces with a single space
    text = re.sub(r"[ \t\r\f\v]+", " ", text)
    return text.strip()


class GameController(object):
    """The controller of the game"""

    def __init__(self, config, secrets):
        self.config = config
        self.secrets = secrets
        self.gui = cli_gui.GUI()
        self.db = db.Database()
        self.nlp = self.get_nlp_handler()

        self.game_actions = {
            "r": ("Retry", self.retry_line),
            "e": ("Edit", self.edit_active_line),
            "d": ("Del", self.delete_active_line),
            "a": ("Add", self.add_line),
            "t": ("Title", self.edit_title),
            "s": ("Story", self.edit_story_details),
            "i": ("Instruct", self.edit_instructions),
            "KEY_ENTER": ("Next", self.next_line),
        }

    def run(self):
        with self.gui.activate():
            self.start_mainmenu_loop()

    def start_mainmenu_loop(self):
        choices = {
            "n": ("New game", self.start_new_game),
            "l": ("Load game", self.start_game_lister),
            "c": ("Write config file (config.ini and secrets.ini)",
                  self.edit_config),
        }
        menuwindow = cli_gui.MenuWindow(gui=self.gui, choices=choices)
        while True:
            try:
                choice = menuwindow.activate()
            except cli_gui.UserQuitting:
                return
            else:
                choice[1]()

    def start_game_lister(self):
        choices = {
            'd': ('Delete', self.delete_game),
            'n': ('New', self.start_new_game),
            'KEY_ENTER': ('Load', self.load_game),
        }

        message = None
        while True:
            games = []
            for game in self.db.get_games():
                games.append((game['gameid'], game['title'], 'TODO length'))
            table_viewer = cli_gui.TableEditWindow(self.gui, choices=choices,
                                                   data=games)
            try:
                choice, lineid, game = table_viewer.activate(message=message)
                message = None
            except cli_gui.UserQuitting:
                return
            else:
                message = choice[1](game)

    def load_game(self, selected):
        self.game = Game(db=self.db, nlp=self.nlp,
                         gameid=selected[0])
        gamegui = cli_gui.GameWindow(gui=self.gui, choices=self.game_actions,
                                     game=self.game)
        self.start_game_input_loop(self.game, gamegui, message="Game loaded")

    def delete_game(self, gamedata):
        self.db.delete_game(gamedata[0])
        return "Game deleted"

    def edit_config(self):
        self.config.write(open(default_configfile, "w"))
        self.secrets.write(open(default_secretsfile, "w"))

    def start_new_game(self, _=None):
        self.game = Game(db=self.db, nlp=self.nlp)
        self.game.set_instructions(default_instructions)

        concept = cleanup_text(
            self.gui.start_input_line("A concept for the story (leave blank "
                                      + "for random)? "))
        if not concept:
            concept = self.nlp.prompt("Give me a random concept of an exiting "
                                      + "fantasy story.")
        self.game.set_details(concept)
        title = cleanup_text(self.nlp.prompt(
            "Give me only one title for a story with the given concept, "
            + "without any other feedback: " + concept))
        self.game.set_title(title)
        self.game.add_lines(self.game.get_introduction())
        gamegui = cli_gui.GameWindow(gui=self.gui, choices=self.game_actions,
                                     game=self.game)
        self.start_game_input_loop(self.game, gamegui,
                                   message="New game started")

    def start_game_input_loop(self, game, gamegui, message=None):
        while True:
            try:
                choice, elementid, element = gamegui.activate(message=message)
            except cli_gui.UserQuitting:
                return
            else:
                message = choice[1](game, gamegui, elementid, element)

    def next_line(self, game, gamegui, lineid, oldline):
        """Generate new text"""
        # TODO: move this to gamegui somehow...
        self.gui.send_message("Generating more text...")
        game.generate_next_lines()
        gamegui.set_focus(-1)
        return "New text generated"

    def retry_line(self, game, gamegui, lineid, active_line):
        """Regenerate chosen line"""
        self.gui.send_message("Retry selected text")
        # TODO: handle the given line too, but goes to last line anyway
        game.retry_active_line(lineid)
        return "New text generated, if it was the last..."

    def edit_active_line(self, game, gamegui, lineid, oldline):
        """Edit chosen line/response"""
        newline = self.gui.start_input_edit_text(oldline)
        newline = cleanup_text(newline)
        game.change_line(lineid, newline)
        return "Last line updated"

    def delete_active_line(self, game, gamegui, lineid, oldline):
        """Delete chosen line/response"""
        game.delete_line(lineid)
        gamegui.shift_focus_up()
        return "Line deleted"

    def add_line(self, game, gamegui, lineid, oldline):
        """Write a new line/response"""
        newline = self.gui.start_input_line()
        if newline:
            game.add_lines(newline)
            gamegui.set_focus(-1)
        return "New line added"

    def edit_title(self, game, gamegui, lineid, oldline):
        new_title = self.gui.start_input_edit_text(game.title)
        if new_title:
            game.set_title(new_title)
            return "Title updated"
        else:
            return "Title unchanged"

    def edit_instructions(self, game, gamegui, lineid, oldline):
        new_instructions = self.gui.start_input_edit_text(
            game.instructions)

        if not remove_comments(new_instructions.strip()).strip():
            new_instructions = default_instructions

        game.set_instructions(new_instructions)
        return "Instructions updated"

    def edit_story_details(self, game, gamegui, lineid, oldline):
        new_details = self.gui.start_input_edit_text(game.details)

        if not remove_comments(new_details.strip()).strip():
            new_details = default_details

        game.set_details(new_details)
        return "Story summary updated"

    def get_nlp_handler(self):
        if not hasattr(self, "nlp"):
            model = self.config["DEFAULT"]["nlp_model"]
            extra = None
            if ':' in model:
                model, extra = model.split(':', 1)
            if model in ('local', 'huggingface') and extra is None:
                raise Exception("Missing param for NLP model, after : in conf")
            logger.debug(f"Loading NLP {model!r} with param {extra!r}")
            nlp_class = nlp.get_nlp_class(model)
            self.nlp = nlp_class(secrets=self.secrets, extra=extra)
        return self.nlp


class Game(object):

    def __init__(self, db, nlp, gameid=None):
        self.db = db
        self.nlp = nlp

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

    def set_instructions(self, text):
        """Set the instructions for the NLP generations."""
        self.instructions = cleanup_text(text)
        self.save()

    def set_details(self, text):
        """Set story details and other important information"""
        self.details = cleanup_text(text)
        self.save()

    def set_title(self, new_title):
        self.title = cleanup_text(new_title).strip()
        self.save()

    def add_lines(self, text):
        """Add text to continue the story."""
        text = cleanup_text(text)
        self.lines.append(text)
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

        prompt = cleanup_text(prompt)

        # TODO: check if all APIs support lists of just text
        return cleanup_text(self.nlp.prompt(prompt))

    def get_introduction(self):
        """Make the AI come up with the initial start of the story."""
        prompt = [remove_comments(self.instructions)]
        details = remove_comments(self.details)
        prompt.append(f"\n---\nThe title of the story: '{self.title}'\n")
        if details.strip():
            prompt.append("\n---\nImportant details about the story:\n")
            prompt.append(details)

        prompt.append("\n---\nGive me three sentences that starts this story.")
        return cleanup_text(self.nlp.prompt(prompt))

    def generate_next_lines(self, instructions=None):
        more = self._generate_prompt(instructions)
        self.add_lines(more)
        self.save()
        return more

    def delete_line(self, lineid):
        del self.lines[lineid]
        self.save()

    def retry_active_line(self, lineid):
        if lineid is None or lineid == len(self.lines) - 1:
            # Only support retrying last line for now. Haven't implemented
            # changing inside of the chain yet.
            lineid = len(self.lines) - 1
            self.delete_line(lineid)
            return self.generate_next_lines()
        else:
            print("Can't retry inside, per now")
            logger.warning("Can't retry inside chain, per now")
        self.save()

    def change_line(self, lineid, new_text):
        self.lines[lineid] = new_text
        self.save()


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
