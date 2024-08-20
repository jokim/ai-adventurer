#!/usr/bin/env python

import os

from ai_adventurer import config


def config_to_dict(config):
    ret = {}
    for section in config:
        for key in config[section]:
            ret.setdefault(section, {})
            ret[section][key] = config[section][key]
    return ret


def test_load_empty_configfile():
    config.load_config("", None)


def test_default_config():
    ret = config.load_config("", None)
    assert ret == config.default_config


def test_save_config(tmp_path):
    filename = tmp_path / "conf.ini"
    conf = config.load_config("")
    config.save_config(conf, filename)
    assert os.path.exists(filename)
    conf2 = config.load_config(filename)
    assert conf == conf2


def test_save_edited_config(tmp_path):
    filename = tmp_path / "conf.ini"
    conf = config.load_config("")
    conf.set('DEFAULT', 'nlp_model', 'nonsence')
    config.save_config(conf, filename)
    conf2 = config.load_config(filename)
    assert conf == conf2
    assert 'nonsence' in filename.read_text()
    assert 'nonsence' == conf2.get('DEFAULT', 'nlp_model')
    return


def test_load_empty_secrets():
    config.load_secrets("")


def test_default_secret_settings():
    ret = config.load_secrets("")
    assert ret == config.default_secret_settings


def test_save_secrets(tmp_path):
    filename = tmp_path / "secrets.ini"
    conf = config.load_secrets("")
    config.save_secrets(conf, filename)
    assert os.path.exists(filename)
    conf2 = config.load_secrets(filename)
    assert config_to_dict(conf) == config_to_dict(conf2)
    assert 'CHANGEME' in filename.read_text()


def test_save_secrets_without_missing(tmp_path):
    filename = tmp_path / "conf.ini"
    conf = config.load_secrets("")
    conf.set('DEFAULT', 'openai-key', 'OLDVALUE')
    config.save_secrets(conf, filename)
    conf2 = config.load_secrets(filename)
    assert 'OLDVALUE' == conf2.get('DEFAULT', 'openai-key')
    conf2.set('DEFAULT', 'openai-key', 'NEWVALUE')
    config.save_secrets(conf2, filename)
    conf3 = config.load_secrets(filename)
    assert 'NEWVALUE' == conf3.get('DEFAULT', 'openai-key')
    assert 'OLDVALUE' not in filename.read_text()
