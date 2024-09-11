#!/usr/bin/env python
"""Utility functionality for handling story text.

Mostly to be able to parse and present stories better.

Markdown format is excepted from the input text.

"""

import re
import logging

logger = logging.getLogger(__name__)


class Section(object):
    """A poor mans container for a 'section' of a story.

    There are different types of sections, e.g. a title, which has their own
    subclasses.

    """
    def __init__(self, text):
        self.text = text
        self.selected = False

    def __str__(self):
        return self.text

    def _get_short_text(self, text, maxlength=15):
        """Get a shortened part of given text"""
        if len(text) <= maxlength:
            return text
        return text[0:maxlength] + "…"

    def __repr__(self):
        txt = self._get_short_text(str(self))
        selected = ""
        if self.selected:
            selected = " Selected!"
        return f"<{self.__class__.__name__} '{txt}'{selected}>"


class Paragraph(Section):
    """A paragraph of a story.

    Note that one paragraph can consist of many "sub sections".

    """

    def __init__(self, text):
        """Init

        @type text: str, list of str or list of Section
        @param text:
            The input text should be a list of Section objects. But for
            simplicity a str is accepted and converted.

        """
        if isinstance(text, str):
            text = [Section(text)]
        self.text = text
        self.selected = False

    def __str__(self):
        return " ".join(str(s) for s in self.text)

    def __repr__(self):
        txt = self._get_short_text(str(self))
        selected = ""
        if self.selected:
            selected = " Selected!"
        nr_ele = len(self.text)
        cls_name = self.__class__.__name__
        return f"<{cls_name} elements={nr_ele} '{txt}'{selected}>"


class Header(Section):
    """A title or subtitle in the story.

    Expects the raw input to be in markdown format, i.e. starting with at least
    one '#'.

    """

    def __init__(self, raw):
        self.selected = False
        header = re.match("^(#+) (.*)", raw.strip())
        if not header:
            logger.warning("Unhandled title: %r", raw)
            self.level = None
            self.text = raw
        else:
            self.level = header.group(1)
            self.text = header.group(2)


class Instruction(Section):
    """An 'instruction' from the user.

    TODO: This should be kept out of the story, as it's own type of text, so it
    doesn't have to be parsed out again.

    """

    instruct_text = 'INSTRUCT: '

    def __init__(self, raw):
        raw = raw.strip()
        if raw.startswith(self.instruct_text):
            raw = raw[len(self.instruct_text):]
        super().__init__(raw)


class Story(object):
    """A story that contains all the parts (sections) of a story."""

    def __init__(self, parts, selected_part=None):
        """Convert the game parts into neater paragraphs, with formating.

        @param parts: The game content
        @param selected_part:
            The number of the part that is selected and should be highlighted.
        @rtype tuple
        @return:
            A tuple where the first element is a list with the lines that could
            be printed, and the second is the first *row* that contains the
            selected part.

        """
        self.sections = self._parse_text(parts, selected_part)

    def _parse_text(self, parts, selected_part=None):
        """Parse raw input and convert to sections"""
        past_text = []
        sections = []
        for partnumber, chunk in enumerate(parts):
            for row in chunk.splitlines():
                if not row:
                    # Empty row means a newline, which means a new paragraph
                    if past_text:
                        sections.append(Paragraph(past_text))
                        past_text = []
                elif row.strip().startswith('#'):
                    # A title, most likely
                    # TODO: handle lists? Normally not part of a story
                    if past_text:
                        sections.append(Paragraph(past_text))
                        past_text = []
                    section = Header(row)
                    if partnumber == selected_part:
                        section.selected = True
                    sections.append(section)
                elif row.strip().startswith('INSTRUCT:'):
                    if past_text:
                        sections.append(Paragraph(past_text))
                        past_text = []
                    section = Instruction(row)
                    if partnumber == selected_part:
                        section.selected = True
                    sections.append(section)
                else:
                    section = Section(row)
                    if partnumber == selected_part:
                        section.selected = True
                    past_text.append(section)
        if past_text:
            sections.append(Paragraph(past_text))
        return sections

    def convert_to_urwid(self):
        """Return the parsed story in an urwid combatible format.

        urwid likes text in a tuple format:

            (<palette-name>, <text>)

        So here you get a list of such tuples. Note that some lists even
        consists of lists themselves. But they should all be able to be
        included in a widget.

        @rtype: tuple
        @return:
            First element contains the urwid elements, the second the first
            element that is selected.

        """
        rows = []
        first_row_selected = -1

        for section in self.sections:
            # Add an empty line between paragraphs (except the first)
            if (isinstance(section, (Paragraph, Header, Instruction))
                    and rows
                    and rows[-1] != ""):
                rows.append("")

            if isinstance(section, Header):
                if section.selected:
                    if first_row_selected == -1:
                        first_row_selected = len(rows)
                    rows.append(("selected", str(section)))
                else:
                    rows.append(("chapter", str(section)))
            elif isinstance(section, Instruction):
                if section.selected:
                    if first_row_selected == -1:
                        first_row_selected = len(rows)
                    rows.append(("selected", "I: " + str(section)))
                else:
                    rows.append(("instruction", "I: " + str(section)))
            elif isinstance(section, Paragraph):
                tmp = []
                for txt in section.text:
                    if txt.selected:
                        if first_row_selected == -1:
                            first_row_selected = len(rows) + len(tmp)
                        if tmp:
                            tmp.append(("selected", " "))
                        tmp.append(("selected", str(txt)))
                    else:
                        if tmp:
                            tmp.append(("story", " "))
                        tmp.append(("story", str(txt)))
                rows.append(tmp)
            else:
                if section.selected:
                    if first_row_selected == -1:
                        first_row_selected = len(rows)
                    rows.append(("selected", str(section)))
                else:
                    rows.append(("story", str(section)))
        return rows, first_row_selected
        # And then, recalculate the position of the row, in case the size has
        # made a row to break into several lines
        # real_row = 0
        # if self._cached_size:
        #     maxcols, _ = self._cached_size
        #     if maxcols:
        #         for i, row in enumerate(rows):
        #             if i >= first_row_selected:
        #                 break
        #             # The row could contain a formatter
        #             if isinstance(row, tuple):
        #                 row = row[1]
        #             # Special case for Paragraphs:
        #             if isinstance(row, list):
        #                 tmp = ""
        #                 row =
        #             try:
        #                 real_row += len(textwrap.wrap(row, maxcols))
        #             except Exception as e:
        #                 print(row)
        #                 raise e
