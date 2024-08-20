#!/usr/bin/env python

import configparser


default_configfile = "config.ini"
default_secretsfile = "secrets.ini"

default_config = {
    "DEFAULT": {
        # See ai_adventurer/nlp.py for available models
        "nlp_model": "gemini-1.5-flash",
    },
}


default_secret_settings = {
    "DEFAULT": {
        "openai-key": "CHANGEME",
        "gemini-key": "CHANGEME",
        "mistral-key": "CHANGEME",
    },
}


def load_config(config_file, args=None):
    """Using a simple INI file by now"""

    config = configparser.ConfigParser()
    config.read_dict(default_config)
    config.read(config_file)

    # Override with command-line arguments
    if args:
        if args.nlp_model:
            config["DEFAULT"]["nlp_model"] = args.nlp_model

    return config


def save_config(config, filename=None):
    if filename is None:
        filename = default_configfile
    config.write(open(filename, 'w'))


def save_secrets(config, filename=None):
    if filename is None:
        filename = default_secretsfile
    config.write(open(filename, 'w'))


def load_secrets(config_file):
    """I like to have the secrets separated from the rest of the config."""
    config = configparser.ConfigParser()
    config.read_dict(default_secret_settings)
    config.read(config_file)

    # Not passing any variables as script arguments, since these are secrets.
    return config