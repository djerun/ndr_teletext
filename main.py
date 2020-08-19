"""
curses based NDR TEXT reader

this application reads data from the frontent of tubotext by zoom.de which is
providing the NDR TEXT on the NDR website `https://www.ndr.de` as of August 2020
"""

from datetime import datetime as dt
from functools import partial, reduce
from itertools import count
import operator
import sys
from urllib.request import Request, urlopen

from blessed import Terminal
from bs4 import BeautifulSoup

APP_WIDTH = 40
APP_HEIGHT = 24

BASE_URL = "https://www.ndr.de"
APP_URL = f"{BASE_URL}/public/teletext"
PAGES_URL = f"{APP_URL}/pages.js"
START_PAGE = 100

class Teletext(): # pylint: disable=too-many-instance-attributes
    """
    Teletext Application

    `handle_events` is to be called by the event loop

    :param terminal: blessed.Terminal
    """
    def __init__(self, terminal):
        self.t = terminal # pylint: disable=invalid-name
        self.width = APP_WIDTH
        self.height = APP_HEIGHT
        self.app_url = APP_URL
        self.pages_url = PAGES_URL
        self.start_page = START_PAGE
        self.page = self.start_page
        self.sub_page = 1
        self.current_input = []
        self.page_info = None
        self.min_page = 100
        self.max_page = 899
        self.soup = None
        self.history = []

        self.get_page_info()
        self.load(self.start_page)
        self.display_clock()

    def clear(self):
        """
        clears the terminal and returns the cursor to (0, 0)
        """
        print(self.t.home + self.t.clear)

    def get_offset(self): # pylint: disable=no-self-use # TODO
        """
        returns the offset of the top left corner to center the application in the terminal

        :return: (x_offset, y_offset)
        """
        # TODO
        return (0, 0)

    def classes_to_color_formatter(self, classes):
        """
        generates a blessed color formatter from css classes
        as per `https://www.ndr.de/resources/css/ttx.css`

        other classes are ignored, last foreground and last background class win
        default background is black
        default foreground is white

        :param classes: Iterable with css class names as strings
        """
        colors = {
            '0': 'black',
            '1': 'red',
            '2': 'green',
            '3': 'yellow',
            '4': 'blue',
            '5': 'magenta',
            '6': 'cyan',
            '7': 'white'
        }

        fgc = '7'
        bgc = '0'

        for class_ in classes:
            if class_ in {'b0', 'b1', 'b2', 'b3', 'b4', 'b5', 'b6', 'b7'}:
                bgc = class_[1]
            elif class_ in {'f0', 'f1', 'f2', 'f3', 'f4', 'f5', 'f6', 'f7'}:
                fgc = class_[1]

        formatter_name = f'{colors[fgc]}_on_{colors[bgc]}'

        return self.t.__getattr__(formatter_name)

    def display_clock(self):
        """
        Display date and time on the terminal
        """
        offset = self.get_offset()
        now = dt.now()
        print(self.t.white_on_black(
            f'{self.t.move_xy(offset[0]+25, offset[1])}{"%02d"%(now.day,)}.{"%02d"%(now.month,)}. '
            f'{"%02d"%(now.hour,)}:{"%02d"%(now.minute,)}:{"%02d"%(now.second,)} '
            ))

    def display_page(self):
        """
        Display the current page to the terminal
        """
        self.clear()

        ttx = self.soup.html.body.div
        hdr, txt = list(filter(lambda a: a.name == 'pre', ttx.children))

        offset = self.get_offset()
        print(self.t.move_xy(offset[0], offset[1])+self.t.white_on_black(hdr.text))
        lines = []
        current_line = []
        for element in txt.children:
            if element.name == 'b':
                if reduce(operator.add, map(
                        lambda a: len(a.text), current_line), 0) + len(element.text) > self.width:
                    lines.append(current_line)
                    current_line = []
                current_line.append(element)
        lines.append(current_line)

        for i, line in zip(count(), lines):
            print(
                self.t.move_xy(offset[0], offset[1]+i+1)
                + ''.join(map(
                    lambda a: self.classes_to_color_formatter(a.get('class', []))(a.text),
                    line
                    ))
                + self.classes_to_color_formatter(['f7', 'b0'])(' ')
                )

    def get_page_info(self):
        """
        get the list of existing pages and their number of sub pages
        """
        request = Request(self.pages_url)
        try:
            response = urlopen(request)
            data_string = response.read().decode().split('{')[1].split('}')[0]
            self.page_info = dict(map(
                lambda a: list(map(int, a.split(':'))),
                data_string.split(',')
                ))
        except Exception as error: # pylint: disable=broad-except
            sys.stderr.write(repr(error))

    def load(self, page, sub_page=None, no_history=False):
        """
        load and display a page

        :param page: int number of the page to load
        :param sub_page: int number of the sub page to load
        :param no_history: boolean weather to skip adding the page visit to the visit history
        """
        if not no_history:
            self.history.append((self.page, self.sub_page))

        if page in self.page_info:
            self.page = page
            if sub_page and 1 <= sub_page <= self.page_info[page]:
                self.sub_page = sub_page
            else:
                self.sub_page = 1
        else:
            # TODO: try to skip over page gaps
            self.page = self.start_page
            self.sub_page = 1

        url = f'{self.app_url}/{self.page}_{"%02d" % (self.sub_page,)}.htm'
        request = Request(url)
        response = urlopen(request)
        self.soup = BeautifulSoup(response.read())
        self.display_page()

    def load_number(self, number):
        """
        accumulate number presses until a page number is completed
        on completing a page number (3 digits) the page is loaded

        :param number: int
        """
        self.current_input.append(number)
        if len(self.current_input) == 3:
            self.load(reduce(lambda a, b: a*10+b, self.current_input))
            self.current_input = []

    def load_previous(self):
        """
        navigates to the previous page
        """
        self.load(self.page - 1)

    def load_next(self):
        """
        navigates to the next page
        """
        self.load(self.page + 1)

    def load_previous_sub_page(self):
        """
        navigates to the previous sub page or page if alreadt on the first sub page
        """
        if self.sub_page > 1:
            self.load(self.page, self.sub_page - 1)
        else:
            self.load(self.page - 1)

    def load_next_sub_page(self):
        """
        navigates to the next sub page or page if already on the last sub page
        """
        if self.sub_page < self.page_info[self.page]:
            self.load(self.page, self.sub_page + 1)
        else:
            self.load(self.page + 1)

    def go_back_in_history(self):
        """
        navigates to the last page visited
        """
        try:
            page, sub_page = self.history.pop()
            self.load(page, sub_page, no_history=True)
        except IndexError:
            pass

    def handle_events(self):
        """
        Waits up to one second for a keypress to handle and update the clock afterwards.
        If no keypress is registered the clock is updated and the function returns.
        """
        with self.t.cbreak(), self.t.hidden_cursor():
            key = self.t.inkey(1)

        if key == '':
            self.display_clock()
            return

        def dummy():
            return

        {
            self.t.KEY_ESCAPE: sys.exit,
            self.t.KEY_BACKSPACE: self.go_back_in_history,
            self.t.KEY_LEFT: self.load_previous,
            self.t.KEY_RIGHT: self.load_next,
            self.t.KEY_DOWN: self.load_previous_sub_page,
            self.t.KEY_UP: self.load_next_sub_page,
            ord('-'): self.load_previous_sub_page,
            ord('+'): self.load_next_sub_page,
            ord('0'): partial(self.load_number, 0),
            ord('1'): partial(self.load_number, 1),
            ord('2'): partial(self.load_number, 2),
            ord('3'): partial(self.load_number, 3),
            ord('4'): partial(self.load_number, 4),
            ord('5'): partial(self.load_number, 5),
            ord('6'): partial(self.load_number, 6),
            ord('7'): partial(self.load_number, 7),
            ord('8'): partial(self.load_number, 8),
            ord('9'): partial(self.load_number, 9),
        }.get(key.code or ord(key), dummy)()
        self.display_clock()

    def exec_(self):
        """
        Runs the event loop of the application

        Does only terminate on an uncaught `Exception` or any `BaseException`.
        """
        while True:
            self.handle_events()


def main():
    """
    Runs the Application
    """
    terminal = Terminal()
    with terminal.fullscreen():
        Teletext(terminal).exec_()


if __name__ == '__main__':
    main()
