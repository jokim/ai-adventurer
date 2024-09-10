#!/usr/bin/env python

# import pytest

from ai_adventurer import textutils as tu


def test_section_init():
    s = tu.Section("Test")
    assert str(s) == "Test"
    assert s.selected is False


def test_paragraph():
    p = tu.Paragraph("Test")
    assert str(p) == "Test"
    p = tu.Paragraph(["Test", "What"])
    assert str(p) == "Test What"
    p = tu.Paragraph(("What", "123", "apple"))
    assert str(p) == "What 123 apple"


def test_header():
    t = tu.Header("# This is a title")
    assert str(t) == "This is a title"
    t = tu.Header("Wrong title")
    assert str(t) == "Wrong title"


def test_instruction():
    i = tu.Instruction("INSTRUCT: Do this")
    assert str(i) == "Do this"
    i = tu.Instruction("And that")
    assert str(i) == "And that"


def test_story():
    s = tu.Story(("One", "Two"))
    assert s


def test_story_urwid():
    s = tu.Story(("One", "Two"))
    u, first = s.convert_to_urwid()
    print(u)
    assert u == [[("story", "One"), ("story", " "), ("story", "Two")]]
