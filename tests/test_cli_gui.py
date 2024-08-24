#!/usr/bin/env python

from ai_adventurer import cli_gui


def test_load():
    cli_gui.GUI()


def test_convert_simple_line():
    lines = ("This is a sentence",)
    assert cli_gui.convert_gamelines_to_paragraphs(lines) == lines


def test_convert_many_lines():
    lines = ("This is a sentence.", "And this is another one.")
    assert (cli_gui.convert_gamelines_to_paragraphs(lines) ==
            ("This is a sentence. And this is another one.",))


def test_convert_paragraph():
    lines = (
        "This is a story. And this is a sentence.",
        "Together they make a paragraph.\n\n",
        "While this is another paragraph."
    )
    answer = ((lines[0].strip() + " " + lines[1].strip()),
              lines[2].strip())
    assert cli_gui.convert_gamelines_to_paragraphs(lines) == answer


def test_convert_several_paragraph_in_one_line():
    lines = (
        "One.\n\nTwo.\n\nAnd",
        "three.\n\nWhile four,",
        "and five.",
    )
    answer = (
        "One.",
        "Two.",
        "And three.",
        "While four, and five.",
    )
    assert cli_gui.convert_gamelines_to_paragraphs(lines) == answer
