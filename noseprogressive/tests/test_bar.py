"""Tests for the progress bar"""
# TODO: Running these on a tty of type "xterm" fails.

from StringIO import StringIO

from blessings import Terminal
from nose.tools import eq_

from noseprogressive.bar import ProgressBar


class MockTerminal(Terminal):
    @property
    def width(self):
        return 50

    @property
    def height(self):
        return 24


class MonochromeTerminal(MockTerminal):
    """Work around color reporting never going back to 0 once it's been 256."""
    @property
    def number_of_colors(self):
        return 0


def test_color_bar_half():
    """Assert that a half-filled 16-color bar draws properly."""
    out = StringIO()
    term = MockTerminal(kind='xterm-256color', stream=out, force_styling=True)
    bar = ProgressBar(28, term)

    bar.update('HI', 14)
    eq_(out.getvalue(), u'\x1b7\x1b[25d\x1b[1mHI                                '
                         '\x1b(B\x1b[m  \x1b[100m       \x1b(B\x1b[m'
                         '\x1b[47m       \x1b(B\x1b[m\x1b8')


def test_color_bar_full():
    """Assert that a complete 16-color bar draws properly."""
    out = StringIO()
    term = MockTerminal(kind='xterm-256color', stream=out, force_styling=True)
    bar = ProgressBar(28, term)

    bar.update('HI', 28)
    eq_(out.getvalue(), u'\x1b7\x1b[25d\x1b[1mHI                                '
                         '\x1b(B\x1b[m  \x1b[100m              \x1b(B\x1b[m'
                         '\x1b[47m\x1b(B\x1b[m\x1b8')


def test_monochrome_bar():
    """Assert that the black-and-white bar draws properly when < 16 colors are available."""
    out = StringIO()
    term = MonochromeTerminal(kind='xterm', stream=out, force_styling=True)
    assert term.number_of_colors < 16
    bar = ProgressBar(28, term)

    bar.update('HI', 14)
    eq_(out.getvalue(), u'\x1b7\x1b[25d\x1b[1mHI                                '
                         '\x1b(B\x1b[m  \x1b[7m       \x1b(B\x1b[m'
                         '_______\x1b8')
