from cStringIO import StringIO
from curses import tigetstr, tparm
import sys

from nose.tools import eq_

# This tests that __all__ is correct, since we use below everything that should
# be imported:
from noseprogressive.terminal import *


def test_capability():
    """Check that a capability lookup works.

    Also test that Terminal grabs a reasonable default stream. This test
    assumes it will be run from a tty.

    """
    sc = tigetstr('sc')
    t = Terminal()
    eq_(t.save, sc)
    eq_(t.save, sc)  # Make sure caching doesn't screw it up.


def test_capability_without_tty():
    """Assert capability templates are '' when stream is not a tty."""
    t = Terminal(stream=StringIO())
    eq_(t.save, '')


def test_parametrization():
    """Test parametrizing a capability."""
    eq_(Terminal().cup(3, 4), tparm(tigetstr('cup'), 3, 4))


def height_and_width():
    """Assert that ``height_and_width()`` returns ints."""
    h, w = height_and_width()
    assert isinstance(int, h)
    assert isinstance(int, w)


def test_stream_attr():
    """Make sure Terminal exposes a ``stream`` attribute that defaults to something sane."""
    eq_(Terminal().stream, sys.__stdout__)


def test_position():
    """Make sure ``Position`` does what it claims."""
    # Let the Terminal grab the actual tty and call setupterm() so things work:
    t = Terminal()

    # Then rip it away, replacing it with something we can check later:
    output = t.stream = StringIO()
    
    with Position(3, 4, term=t):
        output.write('hi')

    eq_(output.getvalue(), tigetstr('sc') +
                           tparm(tigetstr('cup'), 4, 3) +
                           'hi' +
                           tigetstr('rc'))
