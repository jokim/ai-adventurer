#!/usr/bin/env python

from ai_adventurer import run
from ai_adventurer import config


def test_gamecontroller_load():
    run.GameController(config._get_default_config(),
                       config._get_default_secrets())
