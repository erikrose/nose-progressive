"""Facilities for wrapping stderr and stdout and dealing with the fallout"""

from __future__ import with_statement
import __builtin__
import cmd
import pdb
import sys


def cmdloop(self, *args, **kwargs):
    """Call pdb's cmdloop, making readline work.

    Patch raw_input so it sees the original stdin and stdout, lest
    readline refuse to work.

    The C implementation of raw_input uses readline functionality only if
    both stdin and stdout are from a terminal AND are FILE*s (not
    PyObject*s): http://bugs.python.org/issue5727 and
    https://bugzilla.redhat.com/show_bug.cgi?id=448864

    """
    def unwrapping_raw_input(*args, **kwargs):
        """Call raw_input(), making sure it finds an unwrapped stdout."""
        wrapped_stdout = sys.stdout
        sys.stdout = wrapped_stdout.stream

        ret = orig_raw_input(*args, **kwargs)

        sys.stdout = wrapped_stdout
        return ret

    orig_raw_input = raw_input
    if hasattr(sys.stdout, 'stream'):
        __builtin__.raw_input = unwrapping_raw_input
    # else if capture plugin has replaced it with a StringIO, don't bother.
    try:
        # Interesting things happen when you try to not reference the
        # superclass explicitly.
        ret = cmd.Cmd.cmdloop(self, *args, **kwargs)
    finally:
        __builtin__.raw_input = orig_raw_input
    return ret


def set_trace(*args, **kwargs):
    """Call pdb.set_trace, making sure it receives the unwrapped stdout.

    This is so we don't keep drawing progress bars over debugger output.

    """
    # There's no stream attr if capture plugin is enabled:
    out = sys.stdout.stream if hasattr(sys.stdout, 'stream') else None

    # Python 2.5 can't put an explicit kwarg and **kwargs in the same function
    # call.
    kwargs['stdout'] = out
    debugger = pdb.Pdb(*args, **kwargs)

    # Ordinarily (and in a silly fashion), pdb refuses to use raw_input() if
    # you pass it a stream on instantiation. Fix that:
    debugger.use_rawinput = True

    debugger.set_trace(sys._getframe().f_back)


class StreamWrapper(object):
    """Wrapper for stdout/stderr to do progress bar dodging"""
    # An outer class so isinstance() works in begin()

    def __init__(self, stream, plugin):
        self.stream = stream
        self._plugin = plugin

    def __getattr__(self, name):
        return getattr(self.stream, name)

    def write(self, data):
        if hasattr(self._plugin, 'bar'):
            with self._plugin.bar.dodging():
                self.stream.write(data)
        else:
            # Some things write to stderr before the bar is inited.
            self.stream.write(data)
