#!/usr/bin/env python
""" The games GUI functionality.

Making use of `blessed` to have a more fancy CLI.

"""

import logging
import re
import subprocess
import tempfile

from blessed import Terminal

logger = logging.getLogger(__name__)


class UserQuitting(Exception):
    """Signalling the user quitting e.g. a menu"""

    pass


class GUI(object):
    """The main GUI of the game.

    Supposed to be the main part the *controller* controls the GUI
    through.

    """

    def __init__(self):
        self.term = Terminal()

    def activate(self):
        """Activate fullscreen mode of the terminal"""
        return self.term.fullscreen()

    def start_input_key(self):
        """Shortcut for waiting for user key input."""
        with self.term.cbreak(), self.term.hidden_cursor():
            return self.term.inkey()

    def start_input_line(self, question="Add a new line: "):
        """Ask the user to write a line."""
        print(
            self.term.move_xy(0, self.term.height - 2) + self.term.clear_eol,
            end="",
        )
        newline = input(question).strip()
        return newline

    def start_input_confirm(self, question="Are you sure?", suffix=" (y/N): "):
        """Ask the user a yes/no-question and return the boolean answer"""
        answer = self.start_input_line(question + suffix)
        if answer == 'y':
            return True
        return False

    def start_input_edit_text(self, old_text):
        """Ask user to edit given text and return the new one."""
        # Just make use of an editor instead
        with tempfile.NamedTemporaryFile(mode="w+", suffix=".txt") as tmpfile:
            tmpfile.write(old_text)
            tmpfile.flush()

            # TODO: Choose your preferred editor, adjust the command
            # accordingly
            editor_command = ["vim", tmpfile.name]
            subprocess.run(editor_command)

            tmpfile.seek(0)
            new_text = tmpfile.read()

        return new_text

    def start_input_menu(self, choices, title=None, endkey="q"):
        """Ask the user to chose an option, and return that.

        The choice format: keys are the character to push for its choice, and
        the values are tuples, where the first must be a human readable name.
        The rest is ignored by this method. Example:

            'n': ('New game', ...),

        The quit option (`endkey`) handled specially, raising UserQuitting.

        """
        status = None
        new_choices = choices.copy()
        new_choices[endkey] = ("Quit", None)
        while True:
            self.print_menu(new_choices, title=title, status=status)
            inp = self.start_input_key()
            if inp in choices:
                return choices[inp]
            elif inp.name in choices:
                # This is for characters like 'ENTER_KEY'
                return choices[inp.name]
            elif inp == endkey:
                raise UserQuitting()
            else:
                status = f"You chose badly: {inp!r}"

    def print_menu(self, choices, title=None, status=None):
        """Print a menu with the given choices."""
        self._print_header(title=title)

        for key, options in choices.items():
            if key == "KEY_ENTER":
                key = "Enter"
            print(self.term.bold(str(key)) + " - " + options[0])
        print()
        if status:
            print()
            print(status)
        # TODO: Any footer to print?

    def send_message(self, message):
        # TODO: move this to GameWindow somehow
        """Send a message to the status field on the screen"""
        print(self.term.move_xy(1, self.term.height - 3), end="")
        print(message, end="")


class Window(object):
    """Managing the terminal as a windows with something.

    Subclasses handles more specific types of data/text.

    Thought behind the flow:

    - Initiate object with proper data and users choices
    - .activate() prints and waits for user input
    - Special input, like moving up or down, is handled by the object
    - The users choice is returned. This means the controller needs to loop
      over `.activate()` if you expect the user to do more in the window

    """

    game_title = "AI adventurer"

    def __init__(self, gui, choices, endkey="q"):
        self.gui = gui
        self.term = gui.term
        self.choices = choices
        self.endkey = endkey
        self.internal_choices = {endkey: ("Quit", None)}

    def activate(self, message=None):
        pass

    def _print_header(self, title=None):
        """Clears the screen and adds the header line"""
        if title:
            title = f"{title} - {self.game_title}"
        else:
            title = self.game_title
        title = self.term.truncate(title, width=self.term.width)

        # Blank out the screen, to make sure old data is removed. This is
        # probably the wrong solution.
        with self.term.location(0, 0):
            for i in range(self.term.height):
                print(self.term.ljust(self.term.on_black(" "),
                                      width=self.term.width))

        print(self.term.home + self.term.on_black + self.term.clear, end="")
        print(self.term.black_on_darkorange_bold(
              self.term.ljust(self.term.black_on_darkorange_bold(title))))

    def _get_footer_content(self, message=None):
        ret = []
        ret.append(self.term.move_xy(0, self.term.height - 2))
        ret.append(self.term.black_on_darkorange)
        ret.append(self.term.ljust(message or ""))
        ret.append("\n")

        choices = self.choices.copy()
        choices.update(self.internal_choices)

        submenu = []
        for key, data in choices.items():
            if key == "KEY_ENTER":
                key = "Enter"
            submenu.append(
                self.term.darkgray_on_darkorange("[")
                + self.term.black_on_darkorange_bold(key)
                + self.term.darkgray_on_darkorange("]")
                + self.term.black_on_darkorange(data[0])
            )
        ret.append(self.term.black_on_darkorange(self.term.ljust(
            self.term.black_on_darkorange(" ").join(submenu),
            width=self.term.width)))
        retout = "".join(ret)
        return retout

    def _print_footer_menu(self, message=None):
        print(self._get_footer_content(message=message), end="")


class MenuWindow(Window):
    """Simple menu window"""

    def activate(self, message=None):
        super().activate(message=message)
        while True:
            self._print_screen(message=message)
            inp = self.gui.start_input_key()
            if inp in self.choices:
                return self.choices[inp]
            elif inp.name in self.choices:
                # This is for characters like 'ENTER_KEY'
                return self.choices[inp.name]
            elif inp == self.endkey:
                raise UserQuitting()
            else:
                message = f"You chose badly: {inp!r}"

    def _print_screen(self, message=None):  # title=None TODO
        """Print a menu with the given choices."""
        self._print_header()

        choices = self.choices.copy()
        choices.update(self.internal_choices)
        for key, options in choices.items():
            if key == "KEY_ENTER":
                key = "Enter"
            print(self.term.bold(str(key)) + " - " + options[0])
        if message:
            print()
            print(message)


class EditorWindow(Window):
    """Handles data with more editor functionality"""

    def __init__(self, gui, choices, data):
        super().__init__(gui, choices)
        self.data = data
        self.focus = 0
        self.internal_choices.update(
            {
                "j": ("Down", None),
                "k": ("Up", None),
            }
        )

    def activate(self, message=None):
        while True:
            self._print_screen(message=message)
            message = None
            key = self.gui.start_input_key()
            if key == "q":
                raise UserQuitting()
            elif key == "j":
                self.shift_focus_down()
                continue
            elif key.name == "KEY_RIGHT":
                self.shift_focus_down(10)
                continue
            elif key.name == "KEY_DOWN":
                self.shift_focus_down()
                continue
            elif key.name == "KEY_PGDOWN":
                self.shift_focus_down(10)
                continue
            elif key == "k":
                self.shift_focus_up()
                continue
            elif key.name == "KEY_UP":
                self.shift_focus_up()
                continue
            elif key.name == "KEY_LEFT":
                self.shift_focus_up(10)
                continue
            elif key.name == "KEY_PGUP":
                self.shift_focus_up(10)
                continue
            elif key.name == "KEY_HOME":
                self.set_focus(0)
                continue
            elif key.name == "KEY_END":
                self.set_focus(-1)
                continue
            elif key in self.choices:
                return (
                    self.choices[key],
                    self.focus,
                    self._get_element(self.focus),
                )
            elif key.name in self.choices:
                return (
                    self.choices[key.name],
                    self.focus,
                    self._get_element(self.focus),
                )
            else:
                message = f"Unknown choice: {key!r}"

    def _get_elements(self):
        """Get the data that the user could manage. Subclass!"""
        return self.data

    def _get_element(self, elementid):
        if not self.data:
            return None
        return self.data[elementid]

    def shift_focus_down(self, jumps=1):
        # The list starts at 0 at the top, so we increase
        self.focus += jumps
        # Don't pass the last line
        if self.focus > len(self._get_elements()) - 1:
            self.focus = len(self._get_elements()) - 1

    def shift_focus_up(self, jumps=1):
        # The list starts at 0 at the top, so we decrease
        self.focus -= jumps
        if self.focus < 0:
            self.focus = 0

    def set_focus(self, elementid):
        assert isinstance(elementid, int) and elementid >= -1
        if elementid == -1:
            self.focus = len(self._get_elements()) - 1
        else:
            self.focus = elementid


class TableEditWindow(EditorWindow):
    """View a simple table with data the user has _simple_ actions on.

    table_data must be a list with lists. Each element is a row, and the
    internal items gets into columns.

    """

    def __init__(self, gui, choices, data):
        super().__init__(gui=gui, choices=choices, data=data)
        # TODO: change to something better than this!
        self.format = (
            "%5d ",
            "%-60s ",
            "%6s",
        )

    def _print_screen(self, message=None):
        """Print the table view"""
        self._print_header()

        for i, line in enumerate(self.data):
            if i == self.focus:
                print(self.term.standout, end="")
            txt = ""
            for i, element in enumerate(line):
                formatter = self.format[i]
                txt += formatter % (element,)
            print(txt + self.term.normal)
        self._print_footer_menu(message=message)


class GameWindow(EditorWindow):

    text_width = 120

    def __init__(self, gui, choices, game):
        super().__init__(gui=gui, choices=choices, data=game)

    def _print_screen(self, message=""):
        """Print the game screen, with all details."""
        self._print_header(title=self.data.title)
        self._print_gamedata()
        self._print_footer_menu(message=message)
        return

    def _get_elements(self):
        return self.data.lines

    def _get_element(self, elementid):
        if not self.data.lines:
            return None
        return self.data.lines[elementid]

    def gamelines_to_paragraphs(self, lines, focus, width=None):
        """Convert the game lines into neater paragraphs, with formating.

        @param lines: The game content
        @param focus:
            The line number that has focus and should be highlighted. Set to
            None to disable.
        @rtype list
        @return:
            A list with the lines that could be printed.

        """
        if not width:
            width = self.text_width

        lines = lines.copy()

        class Section(object):
            def __init__(self, text):
                self.text = text
                self.focus = False

            def __str__(self):
                return self.text

        class Paragraph(Section):
            def __init__(self, text):
                if isinstance(text, str):
                    text = [Section(text)]
                self.text = text
                self.focus = False

            def __str__(self):
                return " ".join(str(s) for s in self.text)

        class Header(Section):
            def __init__(self, title):
                self.focus = False
                header = re.match("^(#+) (.*)", title.strip())
                if not header.group:
                    logger.warn("Unhandled title: %r", title)
                    self.level = None
                    self.title = title
                else:
                    self.level = header.group(1)
                    self.title = header.group(2)

            def __str__(self):
                return self.title

        class Instruction(Section):

            instruct_text = 'INSTRUCT: '

            def __init__(self, text):
                text = text.strip()
                if text.startswith(self.instruct_text):
                    text = text[len(self.instruct_text):]
                super().__init__(text)

        # First, identity the sections, like paragraphs and headers
        sections = []
        past_text = []
        for linenumber, chunk in enumerate(lines):
            for row in chunk.splitlines():
                # Empty row means a newline, which means a new paragraph:
                if not row:
                    if past_text:
                        sections.append(Paragraph(past_text))
                        past_text = []
                elif row.strip().startswith('#'):
                    if past_text:
                        sections.append(Paragraph(past_text))
                        past_text = []
                    section = Header(row)
                    if linenumber == focus:
                        section.focus = True
                    sections.append(section)
                elif row.strip().startswith('INSTRUCT:'):
                    if past_text:
                        sections.append(Paragraph(past_text))
                        past_text = []
                    section = Instruction(row)
                    if linenumber == focus:
                        section.focus = True
                    sections.append(section)
                else:
                    section = Section(row)
                    if linenumber == focus:
                        section.focus = True
                    past_text.append(section)
        if past_text:
            sections.append(Paragraph(past_text))

        # Then, print the sections out into the rows:
        rows = []
        for section in sections:
            # Add an empty line between paragraphs (except the first)
            if (isinstance(section, (Paragraph, Header, Instruction))
                    and rows
                    and rows[-1] != ""):
                rows.append("")
            if isinstance(section, Header):
                text = self.term.darkorange_on_black(f"{section}")
            elif isinstance(section, Instruction):
                text = self.term.darkgray_on_black(f"I: {section}")
            elif isinstance(section, Paragraph):
                text = ""
                for s in section.text:
                    txt = str(s)
                    # Fix bold text:
                    txt = re.sub(r"\*\*(.*?)\*\*", self.term.bold(r"\1"), txt)

                    if text:
                        txt = " " + txt
                    if s.focus:
                        text += self.term.standout(txt)
                    else:
                        text += txt
            else:
                text = str(section)

            if section.focus:
                text = self.term.standout(text)
            rows.extend(self.term.wrap(text, width))
        return rows

    def _print_gamedata(self):
        """Fill main content with the story"""
        y_min = 1
        y_max = self.term.height - 3
        y_pos = y_max
        height = y_max - y_min

        focus = self.focus
        rawlines = self.data.lines

        if len(rawlines) == 0:
            print(self.term.gray("No content yet..."))
            return

        # Focus defaults to -1, which is the last line
        if self.focus == -1:
            focus = len(rawlines) - 1
        # The focus might have moved past the last line
        if self.focus > len(rawlines) - 1:
            focus = len(rawlines) - 1

        lines = self.gamelines_to_paragraphs(rawlines,
                                             focus,
                                             width=min(self.term.width,
                                                       self.text_width))

        # Cut from the top, to reach the focused part
        # Might consider a new variable for scrolling, but a quick workaround
        # for now... In case a section is too long for the screen.

        if len(lines) > height:
            # Special case: If at the bottom:
            if self.focus == -1 or self.focus >= (len(rawlines) - 1):
                cut = len(lines) - height
                lines = lines[cut:]
            else:
                # First, find the line with focus
                linematch = [None, None]
                for i, line in enumerate(lines):
                    if self.term.standout in line:
                        linematch[0] = i
                        break
                for i, line in enumerate(reversed(lines)):
                    if self.term.standout in line:
                        linematch[1] = i
                        break
                # Now, cut around it
                if linematch != [None, None]:
                    cut = max(0, linematch[0] - height)
                    if cut > 0:
                        cut -= linematch[1] - linematch[0]
                        if cut < 0:
                            cut = 0
                    lines = lines[cut:]

        print(self.term.move_xy(0, y_min), end="")
        # TODO: how to make sure that the focused part is in the view?
        y_pos = y_min
        for row in lines:
            if y_pos > y_max:
                break
            print(row)
            y_pos += 1
