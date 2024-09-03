#!/usr/bin/env python
""" The games GUI functionality, using `urwid`.

More features than `blessed`, but still for CLI.

https://urwid.org/

"""

import logging
import random
import re
import subprocess
import tempfile
# import threading
import time

import urwid

logger = logging.getLogger(__name__)


class GUI(object):
    """The main GUI of the game.

    Now using `urwid` as the GUI engine.

    """

    game_title = "AI adventurer"

    def __init__(self):

        # Build the layout
        self.header_text = urwid.Text(("header", self.game_title),
                                      wrap="ellipsis", align="left")
        self.footer_text = urwid.Text(("footer", "Welcome"),
                                      wrap="ellipsis", align="left")

        self.story_box = StoryBox()
        story_body = urwid.Frame(
            header=urwid.AttrMap(self.header_text, "header"),
            body=urwid.AttrMap(self.story_box, "story"),
            footer=urwid.AttrMap(self.footer_text, "footer"),
        )
        self.loop = urwid.MainLoop(story_body,
                                   self.palette,
                                   unhandled_input=self.unhandled_input,
                                   pop_ups=True)
        self.loop.screen.set_terminal_properties(colors=256)

    def activate(self):
        """Activate fullscreen and start the GUI"""
        self.loop.run()

    def quit(self, *args):
        raise urwid.ExitMainLoop()

    def unhandled_input(self, key: str) -> None:
        """Handle input that is not handled by widgets?

        Or is this always called? According to urwids docs, I think it always
        comes here first, since it starts at the top?

        """
        if key in {'q', 'Q'}:
            raise urwid.ExitMainLoop()
        # self.header_text.set_text(("header",
        #                            key + " - " + self.game_title))
        logger.debug(f"Unhandled input: {key!r}")

    # urwid has a palette in the form of tuples:
    # 1. name of attribute (can be anything I want?)
    # 2. foreground color (16-color)
    # 3. background color
    # 4. monochrome settings (optional)
    # 5. foreground for 88 and 256 colors (optional)
    # 6. background for 88 and 256 colors (optional)
    palette = [
        ("header", "black,bold", "dark blue", "", "#000,bold", "#f90"),
        ("title",  "black,bold", "dark blue", "", "#000,bold", "#f90"),
        ("footer", "black,bold", "dark blue", "", "#000,bold", "#f90"),
        ("story", "white", "dark blue", "", "#fff", "#000"),
        ("selected", "black", "white", "", "#000", "#fff"),
        ("reversed", "black,bold", "white", "", "#000,bold", "#fff"),
        ("question", "white,bold", "dark gray", "", "#fff,bold", "#000"),
        ("chapter", "black,bold", "dark blue", "", "#000,bold", "#f90"),
        ("instruction", "light gray", "black", "", "#bbb", "#222"),
        ("flame", "light red", "", "", "#f90", ""),
        # ("streak", "black", "dark red"),
        # ("bg", "white", "dark blue", "", "#fff", "#000"),
    ]

    def set_header(self, text=""):
        if not text:
            text = self.game_title
        else:
            if isinstance(text, (tuple, list)):
                # Could be using urwid formatter format
                text = text[1]
            text = " - ".join((text, self.game_title))
        self.header_text.set_text(("header", text))

    def load_game(self, game, choices):
        """Change the viewer to the game window"""
        self.game = game
        self.set_header(self.game.title)

        self.story_box.choices = choices
        story_body = urwid.Frame(
            header=urwid.AttrMap(self.header_text, "header"),
            body=urwid.AttrMap(self.story_box, "story"),
            footer=urwid.AttrMap(self.footer_text, "footer"),
        )
        self.story_box.load_game(game)
        self.loop.widget = story_body

    def load_mainmenu(self, choices):
        """Set up and present the main menu.

        Callbacks should be added to the menu options, for starting the
        options.

        """
        main = urwid.Padding(Menu("AI adventurer", choices),
                             left=1, right=1)

        class Flame(urwid.Text):
            """Simulating a flame"""

            def __init__(self):
                super().__init__(self.get_flame())

            def get_flame(self):
                """Get a random flame"""
                return ("flame", "\n".join(random.choice(self.flames)))

            def regenerate_flame(self):
                self.set_text(self.get_flame())

            flames = (
                (
                    r"   )   ",
                    r"  ) \  ",
                    r" / ) ( ",
                    r" \(_)/ ",
                ),
                (
                    r"   (   ",
                    r"  / (  ",
                    r" ( / \ ",
                    r" \(.)/ ",
                ),
                (
                    r"  (    ",
                    r"  )\   ",
                    r" (\ \  ",
                    r" \(.)  ",
                ),
                (
                    r"       ",
                    r"   /\  ",
                    r"  (  \ ",
                    r"  \.)/ ",
                ),
                (
                    r"    )  ",
                    r"   /(  ",
                    r"  (\ \ ",
                    r"  (.)/ ",
                ),
                (
                    r"  /\   ",
                    r" ( ^\  ",
                    r" |/ \( ",
                    r" \(-)/ ",
                ),
                (
                    r"  /^\  ",
                    r" ( _ ) ",
                    r" (/ \( ",
                    r" \(-)/ ",
                ),
                (
                    r"   ^   ",
                    r"  / \  ",
                    r" ( \ ) ",
                    r" \(-)/ ",
                ),
            )

        flamewidgets = (
            ('weight', 10, Flame()),
            ('weight', 80, urwid.Padding(urwid.Text(""))),
            ('weight', 10, Flame()),
        )

        def regenerate_flames(*args, **kwargs):
            for f in flamewidgets:
                if isinstance(f[2], Flame):
                    f[2].regenerate_flame()
            self.loop.draw_screen()

        def regenerate_flame_loop(stop_event):
            while not stop_event.is_set():
                time.sleep(0.1 + random.random() * 2)  # 0.1 - 2.1 seconds
                regenerate_flames()

        background = urwid.Filler(urwid.Columns(flamewidgets, dividechars=3),
                                  valign=("relative", 98))
        self.body = urwid.Overlay(main,
                                  background,
                                  align=urwid.CENTER,
                                  width=(urwid.RELATIVE, 50),
                                  valign=urwid.MIDDLE,
                                  height=(urwid.RELATIVE, 40),
                                  min_width=10,
                                  min_height=5,
                                  )
        self.loop.widget = self.body

        delay = 0.1
        for i in range(1000):
            self.loop.set_alarm_in(delay, regenerate_flames)
            delay += (random.random() * 0.5)

        # stop_event = threading.Event()
        # self.flame_thread = threading.Thread(target=regenerate_flame,
        #                                      args=(stop_event,))
        # self.flame_thread.start()

    def load_gamelister(self, games, choices):
        """Load the game overview"""
        body = urwid.Frame(
            header=urwid.AttrMap(self.header_text, "header"),
            body=GameLister(games=games, choices=choices),
            footer=urwid.AttrMap(self.footer_text, "footer"),
        )
        # urwid.SimpleFocusListWalker(gamelist)))
        self.loop.widget = body

    def start_input_edit_text(self, old_text):
        """Ask user to edit given text and return the new one.

        This is calling the external editor, for now at least. Not sure what's
        best option.

        """
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

        # TODO: sometimes the screen gets weird, not drawn correctly, when
        # returning from the editor (vim at least). Why? Redrawing doesn't seem
        # to work...
        time.sleep(0.5)
        self.loop.draw_screen()
        return new_text

    def start_input_line(self, question="Add a new line: "):
        """Ask the user to write a line"""
        # newline = input(question).strip()
        # return newline

        # TODO: this does not work for now!

        old_body = self.loop.widget

        def on_change(edit: urwid.Edit, new_text: str):
            if "\n" in new_text:
                self.loop.widget = old_body
            # What to do? How to return to correct place?

        body = urwid.Frame(
            # TODO: a function for this?
            header=urwid.AttrMap(self.header_text, "header"),
            body=urwid.AttrMap(urwid.Edit(question), "question"),
            footer=urwid.AttrMap(self.footer_text, "footer"),
        )
        self.loop.widget = body

    def send_message(self, text):
        """Add a message to the user"""
        self.footer_text.set_text(text)

    def ask_confirm(self, question="Are you sure?", callback=None,
                    user_data=None):
        """Ask the user to confirm something.

        If the user confirms, the callback is called. Otherwise the popup is
        removed and it's back to the previous screen.

        """
        launch = ConfirmPopupLauncher(self.loop.widget, question=question,
                                      callback=callback, user_data=user_data)
        self.loop.widget = launch
        launch.open_pop_up()


class Menu(urwid.ListBox):
    """A menu, with easier choices"""

    def __init__(self, title, choices):
        """Init

        @param title: The title of the menu

        @param choices:
            The items in the menu. Should be a dict in the format:

                'keyboard-key': ("Name of element", callback-func),

        """
        self.choices = choices
        self.internal_choices = {
            'j': self.move_down,
            'k': self.move_up,
        }
        title = urwid.Padding(urwid.Text(title), width=("relative", 100))
        self.body = [urwid.AttrMap(title, "title")]
        # TODO: add divider?
        # urwid.Divider()]
        for key, choice in choices.items():
            button = self._create_menu_button(f"{key:4} - {choice[0]}",
                                              choice[1])
            self.body.append(button)
        super().__init__(urwid.SimpleFocusListWalker(self.body))

    def _create_menu_button(self, caption, callback) -> urwid.AttrMap:
        button = urwid.Button(caption, on_press=callback)
        # TODO: add keypress too somewhere?
        return urwid.AttrMap(button, None, focus_map="reversed")

    def keypress(self, size, key):
        if key in self.choices:
            self.choices[key][1](self)
            return
        if key in self.internal_choices:
            self.internal_choices[key]()
            return
        return super().keypress(size, key)

    def move_up(self):
        self.set_focus(max(1, self.focus_position - 1))

    def move_down(self):
        self.set_focus(min(self.focus_position + 1, len(self) - 1))


class StoryBox(urwid.Scrollable):
    """The box that handles the story itself."""

    def __init__(self, widget=None, force_forward_keypress=False, game=None):
        self.internal_choices = {
            'j': ('Move selection one down', self.move_selection_down),
            'k': ('Move selection one up', self.move_selection_up),
            'home': ('Move selection to start', lambda: self.set_selection(0)),
            'end': ('Move selection to last', lambda: self.set_selection(-1)),
            '?': ('Show help', self.open_help_popup),
        }
        if game:
            self.game = game
        self.content = ShowPopup(urwid.Pile([]), title="Available keys")
        self.selected_part = 0
        super().__init__(widget=self.content,
                         force_forward_keypress=force_forward_keypress)

    def load_game(self, game):
        """Load a new game, resetting old settings"""
        self.game = game
        self.set_selection(-1)
        self.load_text()
        self.set_scrollpos(-1)

    def keypress(self, size: 'tuple[int, int]',
                 key: 'str') -> 'str | None':
        logger.debug(f"In StoryBox keypress, with key: {key!r}")
        if key in self.choices:
            self.choices[key][1](self)
            return
        if key in self.internal_choices:
            self.internal_choices[key][1]()
            return
        logger.debug(f"Unhandled key: {key!r}")
        return super().keypress(size, key)

    def move_selection_up(self):
        old_id = self.selected_part
        self.selected_part -= 1
        if self.selected_part < 0:
            self.selected_part = 0

        if old_id != self.selected_part:
            self.load_text()

    def move_selection_down(self):
        old_id = self.selected_part
        self.selected_part += 1
        if self.selected_part >= len(self.game.lines):
            self.selected_part = len(self.game.lines) - 1

        if old_id != self.selected_part:
            self.load_text()

    def set_selection(self, lineid):
        """Set the selection to a certain part"""
        if lineid > len(self.game.lines) or lineid <= -1:
            lineid = len(self.game.lines) - 1

        old_id = self.selected_part
        self.selected_part = lineid
        if old_id != lineid:
            self.load_text()
            if lineid == len(self.game.lines) - 1:
                self.set_scrollpos(-1)
            elif lineid == 0:
                self.set_scrollpos(0)

    def load_text(self):
        """Load in the games story"""
        widgets = []
        rows, select_start = self.gamelines_to_paragraphs(self.game.lines,
                                                          self.selected_part)
        for row in rows:
            widgets.append(urwid.Text(row))
        self.content.original_widget = urwid.Pile(widgets)
        return select_start

    def open_help_popup(self):
        """View a popup with the key shortcuts"""
        values = []
        for key, data in self.choices.items():
            values.append(f"{key:10} - {data[0]}")
        for key, data in self.internal_choices.items():
            values.append(f"{key:10} - {data[0]}")

        self.content.set_popup_content(urwid.Pile([urwid.Text(v) for v in
                                                   sorted(values)]))
        self.content.open_pop_up()

    def gamelines_to_paragraphs(self, parts, selected):
        """Convert the game parts into neater paragraphs, with formating.

        @param parts: The game content
        @param selected:
            The number of the part that is selected and should be highlighted.
        @rtype tuple
        @return:
            A tuple where the first element is a list with the lines that could
            be printed, and the second is the first *row* that contains the
            selected part.

        """
        # TODO: refactor this!

        class Section(object):
            def __init__(self, text):
                self.text = text
                self.selected = False

            def __str__(self):
                return self.text

        class Paragraph(Section):
            def __init__(self, text):
                if isinstance(text, str):
                    text = [Section(text)]
                self.text = text
                self.selected = False

            def __str__(self):
                return " ".join(str(s) for s in self.text)

        class Header(Section):
            def __init__(self, title):
                self.selected = False
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
        for linenumber, chunk in enumerate(parts):
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
                    if linenumber == selected:
                        section.selected = True
                    sections.append(section)
                elif row.strip().startswith('INSTRUCT:'):
                    if past_text:
                        sections.append(Paragraph(past_text))
                        past_text = []
                    section = Instruction(row)
                    if linenumber == selected:
                        section.selected = True
                    sections.append(section)
                else:
                    section = Section(row)
                    if linenumber == selected:
                        section.selected = True
                    past_text.append(section)
        if past_text:
            sections.append(Paragraph(past_text))

        # Then, print the sections out into the rows:
        rows = []
        first_row_selected = -1

        for section in sections:
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
                            first_row_selected = len(rows)
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


class GameLister(urwid.ListBox):
    """The list of existing stories to load or manage"""

    def __init__(self, games, choices):
        self.internal_choices = {
            'j': ('Move down', self.move_down),
            'k': ('Move up', self.move_up),
        }
        self.choices = choices
        gamelist = []
        for game in games:
            button = urwid.Button(game['title'], on_press=game['callback'],
                                  user_data=game)
            button.gamedata = game
            gamelist.append(urwid.AttrMap(button, None, focus_map="reversed"))
        super().__init__(body=gamelist)

    def keypress(self, size, key):
        if key in self.choices:
            self.choices[key][1](self, focused=self.focus)
            return
        elif key in self.internal_choices:
            self.internal_choices[key][1](focused=self.focus)
            return
        return super().keypress(size, key)

    def move_up(self, focused):
        self.set_focus(max(1, self.focus_position - 1))

    def move_down(self, focused):
        self.set_focus(min(self.focus_position + 1, len(self) - 1))


class ShowPopup(urwid.PopUpLauncher):
    """A simple popup to show some text and quit"""

    def __init__(self, original_widget, title=None, popup_content=None):
        super().__init__(original_widget)
        self.title = title
        self.confirm_button = urwid.Button(
            "Ok", on_press=lambda _: self.close_pop_up())
        if popup_content:
            self.set_popup_content(popup_content)
        else:
            self.popup = urwid.LineBox(self.confirm_button, title=self.title)

    def set_popup_content(self, widget):
        """Set or change the content of the popup.

        The LineBox and ok Button is always included.

        """
        self.popup = urwid.LineBox(urwid.Pile([widget, urwid.Divider(),
                                               self.confirm_button]),
                                   title=self.title)

    def create_pop_up(self):
        return self.popup

    def get_pop_up_parameters(self):
        # TODO: fix this, crashes at the wrong sizes!
        width, height = self.popup.pack()
        logger.debug(f"got width {width} and height {height}")
        return {'left': 2, 'top': 2,
                'overlay_width': 'pack',
                'overlay_height': 'pack',
                }


class ConfirmPopupLauncher(urwid.PopUpLauncher):
    """A confirmation popup"""

    def __init__(self, original_widget, question, callback, user_data):
        super().__init__(original_widget)

        def confirmer(widget):
            logger.debug(f"Confirmed delete: {widget}")
            self.close_pop_up()
            callback(self, user_data)

        confirm_button = urwid.Button("Confirm", on_press=confirmer)

        self.popup = urwid.LineBox(
            urwid.Pile([
                urwid.Text(question),
                urwid.Divider(),
                confirm_button,
                urwid.Button("Cancel", on_press=lambda _: self.close_pop_up()),
            ])
        )

    def create_pop_up(self):
        return self.popup

    def get_pop_up_parameters(self):
        logger.debug("Popuplauncher called - get_pop_up_parameters")
        width, height = self.popup.pack()
        return {'left': 2, 'top': 2,
                'overlay_width': width,
                'overlay_height': height}
