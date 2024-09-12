#!/usr/bin/env python

import argparse
import logging
import re

from ai_adventurer import gui_urwid
from ai_adventurer import config
from ai_adventurer import db
from ai_adventurer import nlp


logger = logging.getLogger(__name__)


default_details = """
    % Story summary and details.
    %
    % This is where you could put details that are important for the story. For
    % example a summary of how the story should go, or details about certain
    % characters.
    %
    % All lines starting with hash (#) are ignored.

    % The default is quite generic...
    This is a story about you, going on an adventurous journey. You will
    experience a lot of things, and will be surprised from time to time.

    """


def cleanup_text(text):
    """Remove some unnecessary white space"""
    if isinstance(text, (list, tuple)):
        return [cleanup_text(t) for t in text]
    # Replace multiple newlines with at most two (keeping paragraphs)
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Replace multiple spaces with a single space
    text = re.sub(r"[ \t\r\f\v]+", " ", text)
    return text


def clean_text_for_saving(text):
    text = cleanup_text(text)
    # Remove white space before comments
    ret = []
    for line in text.splitlines():
        ret.append(line.lstrip())
    return "\n".join(ret)


class Controller(object):
    """The controller of the game"""

    def __init__(self, config, secrets):
        self.config = config
        self.secrets = secrets
        self.db = db.Database()
        self.gui = gui_urwid.GUI()

    def run(self):
        self.nlp = self.get_nlp_handler()
        self.start_mainmenu()
        self.gui.activate()

    def start_mainmenu(self, widget=None, focused=None):
        """Call the GUI to present the main menu"""
        choices = {
            "n": ("New game", self.start_new_game),
            "l": ("Load game", self.start_game_lister),
            "c": ("Write config file (config.ini and secrets.ini)",
                  self.edit_config),
            "q": ("Quit", self.gui.quit),
        }
        self.gui.load_mainmenu(choices)

    def start_game_lister(self, widget=None, focused=None):
        choices = {
            'd': ('Delete', self.delete_game),
            'c': ('Copy', self.copy_game),
            'n': ('New', self.start_new_game),
            'q': ('Quit to main menu', self.start_mainmenu),
        }

        games = []
        for game in self.db.get_games():
            game['callback'] = self.load_game
            games.append(game)
        self.gui.load_gamelister(games, choices)

    def load_game(self, widget, user_data, focused=None):
        """Load a given game

        widget and user_data is given by urwids callback regime.

        """
        logger.debug(f"Called load_game: {widget!r}, user_Data: {user_data!r}")
        self.gamec = GameController(db=self.db, nlp=self.nlp, gui=self.gui,
                                    controller=self,
                                    gameid=user_data['gameid'])
        self.gamec.load_game()
        self.gui.send_message("Game loaded. Remember, push ? for help.")

    def delete_game(self, widget, focused):
        gameid = focused.base_widget.gamedata["gameid"]
        title = focused.base_widget.gamedata["title"]

        self.gui.ask_confirm(question=f"Delete game {gameid} - '{title}'?",
                             callback=self.delete_game_confirmed,
                             user_data=gameid)

    def delete_game_confirmed(self, widget, user_data):
        gameid = user_data
        logger.info(f"Deleting game {gameid}")
        self.db.delete_game(gameid)
        self.gui.send_message(f"Game {gameid} deleted")
        # Reload game list, but without resetting the widget, so focus is kept
        games = []
        for game in self.db.get_games():
            games.append({
                'gameid': game['gameid'],
                'title': game['title'],
                'length': 'TODO',
                'callback': self.load_game,
            })
        # TODO: seems like I've not understood something here. How to just
        # remove one line in the body?
        old_pos = min(len(games) - 1,
                      self.gui.loop.widget.base_widget.body.focus_position)
        self.gui.loop.widget.base_widget.body.games = games
        self.gui.loop.widget.base_widget.body.regenerate_body()
        self.gui.loop.widget.base_widget.body.set_focus(old_pos)

    def copy_game(self, widget, focused):
        gameid = focused.base_widget.gamedata["gameid"]
        logger.info(f"Copying game {gameid}")
        if self.db.copy_game(gameid):
            self.gui.send_message("Game copied")
        else:
            self.gui.send_message("Failed to copy")

    def edit_config(self, widget=None, focused=None):
        logger.info("Saving config")
        config.save_config(self.config)
        config.save_secrets(self.secrets)
        self.gui.send_message("Config saved")

    def start_new_game(self, _=None, focused=None):
        self.gamec = GameController(db=self.db, nlp=self.nlp, gui=self.gui,
                                    controller=self)
        self.gamec.start_new_game()

    def get_nlp_handler(self):
        modelname = self.config["DEFAULT"]["nlp_model"]
        try:
            return nlp.NLPHandler(modelname, secrets=self.secrets)
        except nlp.NotAuthenticatedError as e:
            # Ask for API-key and retry
            print(e)
            apikey = input("Input API key: ")
            keyname = nlp.get_nlp_class(modelname).secrets_api_key_name
            self.secrets['DEFAULT'][keyname] = apikey
            answer = input("Want to save this to secrets.ini? (y/N) ")
            if answer == 'y':
                config.save_secrets(self.secrets)
            return nlp.NLPHandler(modelname, secrets=self.secrets)


class GameController(object):
    """The controller of one game/story"""

    def __init__(self, db, nlp, gui, controller, gameid=None):
        self.db = db
        self.nlp = nlp
        self.gui = gui
        self.controller = controller

        self.game_actions = {
            "r": ("Retry active part", self.retry_line),
            "e": ("Edit active part", self.edit_active_line),
            "d": ("Delete active part", self.delete_active_line),
            "a": ("Add new part", self.add_line_dialog),
            "t": ("Edit title of the story", self.edit_title_dialog),
            "s": ("Edit the story details", self.edit_story_details),
            "i": ("Add instruction to the story", self.add_instruction_dialog),
            "I": ("Edit system instructions", self.edit_system_instructions),
            "L": ("Load another game", self.controller.start_game_lister),
            "q": ("Quit and back to mainmenu", self.controller.start_mainmenu),
            "enter": ("Generate new line", self.next_line),
        }
        self.game = Game(db=self.db, gameid=gameid)

    def start_new_game(self):
        """Start the initial dialog for creating a new story"""
        self.game.set_instructions(
            clean_text_for_saving(self.nlp.default_instructions))
        self.gui.ask_oneliner(
            question="A concept for the story (leave blank for random): ",
            callback=self.start_new_game_with_concept)

    def start_new_game_with_concept(self, widget, concept):
        """Continue the new game dialog, after concept input"""
        concept = cleanup_text(concept).strip()
        if not concept:
            concept = self.nlp.prompt_for_concept()
        self.game.set_details(concept)
        title = self.nlp.prompt_for_title(concept)
        self.game.set_title(title)
        self.game.add_lines(self.nlp.prompt_for_introduction(self.game))
        self.gui.load_game(self.game, self.game_actions)

    def load_game(self):
        self.gui.load_game(self.game, self.game_actions)

    def next_line(self, widget):
        """Generate new text"""
        self.gui.send_message("Generating more text...")
        more = self.nlp.prompt_for_next_lines(self.game)
        self.game.add_lines(more)
        self.gui.story_box.set_selection(-1)
        self.gui.send_message("New text generated")

    def retry_line(self, widget):
        """Regenerate chosen line"""
        self.gui.send_message("Retry selected text")
        selected = self.gui.story_box.selected_part

        # Only support retrying last line for now. Haven't implemented changing
        # inside of the chain yet.
        if selected is None or selected == len(self.game.lines) - 1:
            lineid = len(self.game.lines) - 1
            more = self.nlp.prompt_for_next_lines(self.game)
            self.game.delete_line(lineid)
            self.game.add_lines(more)
            self.gui.send_message("Part regenerated, if it was the last…")
            self.gui.story_box.load_text()
        else:
            self.gui.send_message("Can only retry last part")

    def add_line_dialog(self, widget):
        """Start dialog for getting a new line of the story"""
        self.gui.ask_oneliner(
            question="Add new part: ",
            callback=self.add_line)

    def add_line(self, widget, newline):
        """Write a new line/response"""
        if newline.strip():
            self.game.add_lines(newline)
            self.gui.story_box.set_selection(-1)
            self.gui.send_message("New line added")

    def add_instruction_dialog(self, widget):
        """Start dialog for a new instruction"""
        self.gui.ask_oneliner(
            question="Add new instruction: ",
            callback=self.add_instruction)

    def add_instruction(self, widget, newline):
        """Write a new instruction"""
        if newline.strip():
            self.game.add_lines(f"INSTRUCT: {newline}")
            self.gui.story_box.set_selection(-1)
            self.gui.send_message("New line added")

    def edit_title_dialog(self, widget):
        """Start dialog for editing the title"""
        self.gui.ask_oneliner(
            question="Edit title: ",
            callback=self.save_title,
            existing_text=self.game.title,
        )

    def save_title(self, widget, new_title):
        new_title = new_title.strip()
        if new_title:
            self.game.set_title(new_title)
            self.gui.set_header(self.game.title)
            self.gui.send_message("Title updated")
        else:
            self.gui.send_message("Title unchanged")

    def edit_story_details(self, widget):
        new_details = self.gui.start_input_edit_text(self.game.details)

        if not self.nlp.remove_internal_comments(new_details.strip()).strip():
            new_details = clean_text_for_saving(default_details)

        self.game.set_details(new_details)
        self.gui.send_message("Story summary updated")

    def edit_system_instructions(self, widget):
        new_instructions = self.gui.start_input_edit_text(
            self.game.instructions)

        if not self.nlp.remove_internal_comments(
                new_instructions.strip()).strip():
            new_instructions = clean_text_for_saving(
                self.nlp.default_instructions)

        self.game.set_instructions(new_instructions)
        self.gui.send_message("AI instructions updated")

    def edit_active_line(self, widget):
        """Edit chosen line/response"""
        selected = self.gui.story_box.selected_part
        oldline = self.game.lines[selected]
        newline = self.gui.start_input_edit_text(oldline)
        newline = cleanup_text(newline)
        self.game.change_line(selected, newline)
        self.gui.send_message("Last line updated")
        self.gui.story_box.load_text()

    def delete_active_line(self, widget):
        """Delete chosen line/response"""
        selected = self.gui.story_box.selected_part
        self.game.delete_line(selected)
        self.gui.story_box.move_selection_up()
        self.gui.send_message("Line deleted")


class Game(object):
    """The game modeller"""

    def __init__(self, db, gameid=None):
        self.db = db

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

    def delete_line(self, lineid):
        del self.lines[lineid]
        self.save()

    def change_line(self, lineid, new_text):
        self.lines[lineid] = new_text
        self.save()


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
        default=config.default_configfile,
        help="Where the config is located. Default: %(default)s",
    )
    parser.add_argument(
        "--secrets-file",
        type=str,
        metavar="FILENAME",
        default=config.default_secretsfile,
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
        for m in nlp.nlp_models:
            print(m)
        return

    configuration = config.load_config(args.config_file, args)
    secrets = config.load_secrets(args.secrets_file)

    logger.debug("Starting game")
    game = Controller(configuration, secrets)
    game.run()
    logger.debug("Stopping game")


if __name__ == "__main__":
    main()
