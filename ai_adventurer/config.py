#!/usr/bin/env python
"""The configuration of the game.

Only using simple INI files by now.

"""

import configparser


default_configfile = "config.ini"
default_secretsfile = "secrets.ini"

default_config = {
    "nlp": {
        # See ai_adventurer/nlp.py for available models
        "model": "gemini-1.5-flash",
    },
    "story_defaults": {
        "details": """
    § Story summary and details.
    §
    § This is where you could put details that are important for the story. For
    § example a summary of how the story should go, or details about certain
    § characters.
    §
    § All lines starting with section sign (§), or silcrow, are ignored.

    This is a story about you, going on an adventurous journey. You will
    experience a lot of things, and will be surprised from time to time.
        """,
        "instructions": """
    § This is the instructions that is given to the AI before the story.
    § - All lines starting with silcrom (§) are removed for the AI.
    § - Leave the instructions blank to reset to the default instructions.

    You are an excellent story writer assistant, writing remarkable fantasy
    fiction. Do not reply with dialog, only with the answers directly.

    Use markdown format, but use formatting sparsely.

    Writing Guidelines: Use second person perspective and present tense,
    unless the story starts differently. Use writing techniques to bring
    the world and characters to life. Vary what phrases you use. Be
    specific and to the point, and focus on the action in the story. Let
    the characters develop, and bring out their motivations, relationships,
    thoughts and complexity. Keep the story on track, but be creative and
    allow surprising subplots. Include dialog with the characters. Avoid
    repetition and summarisation. Avoid repeating phrases. Use humour.

    If a paragraph starts with "INSTRUCT:", it is not a part of the story,
    but instructions from the user that you must follow when continuing the
    story. Do not add instructions on behalf of the user. Do not include
    the word INSTRUCT in the story.
        """,
    },
}


default_secret_settings = {
    "DEFAULT": {
        "openai-key": "CHANGEME",
        "gemini-key": "CHANGEME",
        "mistral-key": "CHANGEME",
    },
}


def cleanup_whitelines(conf):
    """Remove whitelines which are removed by ConfigParser anyways"""
    for section, items in conf.items():
        for key, value in items.items():
            conf[section][key] = trim_lines(value)


def trim_lines(text):
    ret = ""
    for line in text.splitlines():
        ret += line.strip() + "\n"
    return ret.strip()


def _get_default_config():
    config = configparser.ConfigParser()
    cleanup_whitelines(default_config)
    config.read_dict(default_config)
    return config


def load_config(config_file=None, args=None):
    if config_file is None:
        config_file = default_configfile

    config = _get_default_config()
    config.read(config_file)

    # Override with command-line arguments
    if args:
        if args.nlp_model:
            config["nlp"]["model"] = args.nlp_model

    return config


def save_config(config, filename=None):
    if filename is None:
        filename = default_configfile
    config.write(open(filename, 'w'))


def save_secrets(config, filename=None):
    if filename is None:
        filename = default_secretsfile
    config.write(open(filename, 'w'))


def _get_default_secrets():
    config = configparser.ConfigParser()
    config.read_dict(default_secret_settings)
    return config


def load_secrets(config_file=None):
    """I like to have the secrets separated from the rest of the config."""
    if config_file is None:
        config_file = default_secretsfile

    config = _get_default_secrets()
    config.read(config_file)

    # Not passing any variables as script arguments, since these are secrets.
    return config
