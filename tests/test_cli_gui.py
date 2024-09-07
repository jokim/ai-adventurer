#!/usr/bin/env python

import pytest

from ai_adventurer import gui_urwid
from ai_adventurer import run


def test_load():
    gui_urwid.GUI()


def test_header():
    g = gui_urwid.GUI()
    g.set_header("test")


@pytest.mark.skip(reason="Missing implementation")
def test_convert_simple_line():
    gamec = run.GameController(db.Database(), "TODO")
    s = gui_urwid.StoryBox(game, choices)
    lines = ["This is a sentence",]
    assert s.gamelines_to_paragraphs(lines, None) == lines


@pytest.mark.skip(reason="Missing implementation")
def test_convert_many_lines():
    g = gui_urwid.GUI()
    gw = gui_urwid.GameWindow(g, None, None)
    lines = ["This is a sentence.", "And this is another one."]
    assert (gw.gamelines_to_paragraphs(lines, None) ==
            ["This is a sentence. And this is another one."])


@pytest.mark.skip(reason="Missing implementation")
def test_convert_paragraph():
    g = gui_urwid.GUI()
    gw = gui_urwid.GameWindow(g, None, None)
    lines = [
        "This is a story. And a sentence.",
        "Together they make a paragraph.\n\n",
        "While this is another paragraph."
    ]
    answer = [
        "This is a story. And a sentence. Together they make a paragraph.",
        "",
        "While this is another paragraph."
    ]
    assert gw.gamelines_to_paragraphs(lines, None) == answer


@pytest.mark.skip(reason="Missing implementation")
def test_convert_several_paragraph_in_one_line():
    g = gui_urwid.GUI()
    gw = gui_urwid.GameWindow(g, None, None)
    lines = [
        "One.\n\nTwo.\n\nAnd",
        "three.\n\nWhile four,",
        "and five.",
    ]
    answer = [
        "One.", "",
        "Two.", "",
        "And three.", "",
        "While four, and five.",
    ]
    assert gw.gamelines_to_paragraphs(lines, None) == answer


@pytest.mark.skip(reason="Missing implementation")
def test_convert_with_focus():
    g = gui_urwid.GUI()
    gw = gui_urwid.GameWindow(g, None, None)
    lines = [
        "One.\n\nTwo.\n\nAnd",
        "three.\n\nWhile four,",
        "and five.",
    ]
    answer = [
        "One.", "",
        g.term.standout("Two."), "",
        "And three.", "",
        "While four, and five.",
    ]
    assert gw.gamelines_to_paragraphs(lines, focus=1) == answer


@pytest.mark.skip(reason="Missing implementation")
def test_convert_header():
    g = gui_urwid.GUI()
    gw = gui_urwid.GameWindow(g, None, None)
    lines = [
        "One.\n# Chapter 1\n\nThree.",
        "\n\nWhile four,",
        "and five.",
    ]
    answer = [
        g.term.standout("One."), "",
        g.term.darkorange_on_black("Chapter 1"), "",
        "Three.", "",
        "While four, and five.",
    ]
    assert gw.gamelines_to_paragraphs(lines, focus=0) == answer


@pytest.mark.skip(reason="Missing implementation")
def test_convert_title():
    g = gui_urwid.GUI()
    gw = gui_urwid.GameWindow(g, None, None)
    lines = ["# A title"]
    ret = gw.gamelines_to_paragraphs(lines, None)
    print(ret)
    assert len(ret) == 1
    assert g.term.strip_seqs(ret[0]) == "A title"


@pytest.mark.skip(reason="Missing implementation")
def test_convert_title2():
    g = gui_urwid.GUI()
    gw = gui_urwid.GameWindow(g, None, None)
    lines = ["# A title"]
    answer = ["A title"]
    assert gw.gamelines_to_paragraphs(lines, None) == answer
