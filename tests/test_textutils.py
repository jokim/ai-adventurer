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
    print(s.sections)
    assert len(s.sections) == 1
    s = tu.Story(("One\n", "Two"))
    print(s.sections)
    assert len(s.sections) == 1
    s = tu.Story(("One\n\n", "Two"))
    print(s.sections)
    assert len(s.sections) == 2


def test_story_simple_title():
    s = tu.Story(("# Title",))
    print(s.sections)
    assert len(s.sections) == 1
    assert isinstance(s.sections[0], tu.Header)
    assert str(s.sections[0]) == "Title"


def test_story_selected_first():
    s = tu.Story((
        "# Title\n",
        "And a paragraph",
    ), selected_part=0)
    print(s.sections)
    assert len(s.sections) == 2
    assert isinstance(s.sections[0], tu.Header)
    assert s.sections[0].selected is True


def test_story_selected_second():
    s = tu.Story((
        "# Title\n\n",
        "And a paragraph",
    ), selected_part=1)
    print(s.sections)
    assert isinstance(s.sections[1], tu.Paragraph)
    assert s.sections[0].selected is False
    print(s.sections[1])
    # It's not the paragraph in whole that is selected, but its first (and
    # only) sub section:
    assert s.sections[1].selected is False
    assert s.sections[1].text[0].selected is True


def test_story_selected_third():
    s = tu.Story((
        "# Title\n",
        "\n",
        "A paragraph\n",
        "and more to the previous one.",
    ), selected_part=3)
    print(s.sections)
    assert len(s.sections) == 2
    assert isinstance(s.sections[1], tu.Paragraph)
    assert s.sections[1].selected is False
    assert len(s.sections[1].text) == 2
    assert s.sections[1].text[0].selected is False
    assert s.sections[1].text[1].selected is True


def test_story_urwid():
    s = tu.Story(("One", "Two"))
    u, first = s.convert_to_urwid()
    print(u)
    assert u == [[("story", "One"), ("story", " "), ("story", "Two")]]
