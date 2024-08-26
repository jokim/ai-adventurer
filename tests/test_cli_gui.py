#!/usr/bin/env python

from ai_adventurer import cli_gui


def test_load():
    cli_gui.GUI()


def test_window_load():
    g = cli_gui.GUI()
    cli_gui.Window(g, None)


def test_gamewindow_load():
    g = cli_gui.GUI()
    cli_gui.GameWindow(g, None, None)


def test_convert_simple_line():
    g = cli_gui.GUI()
    gw = cli_gui.GameWindow(g, None, None)

    lines = ["This is a sentence",]
    assert gw.gamelines_to_paragraphs(lines, None) == lines


def test_convert_many_lines():
    g = cli_gui.GUI()
    gw = cli_gui.GameWindow(g, None, None)
    lines = ["This is a sentence.", "And this is another one."]
    assert (gw.gamelines_to_paragraphs(lines, None) ==
            ["This is a sentence. And this is another one."])


def test_convert_paragraph():
    g = cli_gui.GUI()
    gw = cli_gui.GameWindow(g, None, None)
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


def test_convert_several_paragraph_in_one_line():
    g = cli_gui.GUI()
    gw = cli_gui.GameWindow(g, None, None)
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


def test_convert_with_focus():
    g = cli_gui.GUI()
    gw = cli_gui.GameWindow(g, None, None)
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


def test_convert_header():
    g = cli_gui.GUI()
    gw = cli_gui.GameWindow(g, None, None)
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


def test_convert_title():
    g = cli_gui.GUI()
    gw = cli_gui.GameWindow(g, None, None)
    lines = ["# A title"]
    ret = gw.gamelines_to_paragraphs(lines, None)
    print(ret)
    assert len(ret) == 1
    assert g.term.strip_seqs(ret[0]) == "A title"


def test_convert_title2():
    g = cli_gui.GUI()
    gw = cli_gui.GameWindow(g, None, None)
    lines = ["# A title"]
    answer = ["A title"]
    assert gw.gamelines_to_paragraphs(lines, None) == answer
