#!/usr/bin/env python

import pytest
import urwid

from ai_adventurer import gui_urwid
from ai_adventurer import run
from ai_adventurer import db


def test_load():
    gui_urwid.GUI()


def test_header():
    g = gui_urwid.GUI()
    g.set_header("test")


class MockMainLoop(urwid.MainLoop):
    def run(self):
        # Replace this with your custom logic for testing
        pass


def test_simple_run():
    g = gui_urwid.GUI()
    g.loop = MockMainLoop(g.loop.widget, g.palette,
                          unhandled_input=g.unhandled_input)
    g.activate()


def test_simple_exit():
    g = gui_urwid.GUI()
    g.loop = MockMainLoop(g.loop.widget, g.palette,
                          unhandled_input=g.unhandled_input)
    g.activate()
    with pytest.raises(urwid.ExitMainLoop):
        g.quit()


def test_exit_input():
    g = gui_urwid.GUI()
    g.loop = MockMainLoop(g.loop.widget, g.palette,
                          unhandled_input=g.unhandled_input)
    g.activate()
    with pytest.raises(urwid.ExitMainLoop):
        g.unhandled_input(key="q")


def test_storybox_empty():
    game = run.Game(db.MockDatabase())
    s = gui_urwid.StoryBox(game, {})
    s.move_selection_up()
    s.move_selection_up()
    s.move_selection_down()
    s.load_text()
    s.move_selection_down()
    s.move_selection_down()
    s.set_selection(999)
    s.set_selection(1)
    s.load_text()


def test_storybox_oneliner():
    game = run.Game(db.MockDatabase())
    game.add_lines("This is a sentence")
    s = gui_urwid.StoryBox(game, {})
    row = s.load_text()
    assert row == 0
    assert len(s.content.original_widget) > 0


def test_storybox_select_first_row():
    game = run.Game(db.MockDatabase())
    game.add_lines("This is a short sentence")
    s = gui_urwid.StoryBox(game, {})
    s.set_selection(0)
    widgets, row = s._get_story_widgets(width=70)
    assert row == 0
    assert len(widgets) == 1


def test_storybox_select_second_row():
    game = run.Game(db.MockDatabase())
    game.add_lines("One.")
    game.add_lines("Two.")
    s = gui_urwid.StoryBox(game, {})
    s.set_selection(1)
    widgets, row = s._get_story_widgets(width=70)
    assert len(widgets) == 1
    assert row == 0


def test_storybox_select_longer():
    game = run.Game(db.MockDatabase())
    game.add_lines("# Title")
    game.add_lines("First paragraph.\n\n")
    game.add_lines("Second paragraph.\n\n")
    s = gui_urwid.StoryBox(game, {})
    s.set_selection(2)
    widgets, row = s._get_story_widgets(width=70)
    assert len(widgets) == 5
    assert row == 3


def test_storybox_select_longer_and_combined():
    """Test both with many widgets, and some elements on the same row"""
    game = run.Game(db.MockDatabase())
    game.add_lines("# Title")
    game.add_lines("First.")
    game.add_lines("And a tail.\n\n")
    game.add_lines("Second paragraph.\n\n")
    s = gui_urwid.StoryBox(game, {})
    s.set_selection(2)
    widgets, row = s._get_story_widgets(width=70)
    assert len(widgets) == 5
    assert row == 2


@pytest.mark.skip(reason="Missing implementation")
def test_convert_simple_line():
    game = run.Game(db.MockDatabase())
    s = gui_urwid.StoryBox(game, {})
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
