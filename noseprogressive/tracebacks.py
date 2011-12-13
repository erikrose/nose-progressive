"""Fancy traceback formatting"""

import os
from traceback import extract_tb, format_exception_only

from blessings import Terminal
from nose.util import src

from noseprogressive.utils import human_path


def format_traceback(extracted_tb,
                     exc_type,
                     exc_value,
                     cwd='',
                     term=None,
                     function_color=12,
                     dim_color=8,
                     editor='vi'):
    """Return an iterable of formatted traceback frames.

    Also include a pseudo-frame at the end representing the exception itself.

    Format things more compactly than the stock formatter, and make every
    frame an editor shortcut.

    """
    def format_shortcut(editor,
                        file,
                        line,
                        function=None):
        """Return a pretty-printed editor shortcut."""
        return template % dict(editor=editor,
                               line=line,
                               file=file,
                               function=('  # ' + function) if function else '',
                               funcemph=term.color(function_color),
                               # Underline is also nice and doesn't make us
                               # worry about appearance on different background
                               # colors.
                               plain=term.normal,
                               fade=term.color(dim_color) + term.bold)

    if not term:
        term = Terminal()

    if extracted_tb:
        # Shorten file paths:
        for i, (file, line, function, text) in enumerate(extracted_tb):
            extracted_tb[i] = human_path(src(file), cwd), line, function, text

        line_width = len(str(max(the_line for _, the_line, _, _ in extracted_tb)))
        template = ('  %(fade)s%(editor)s +%(line)-' + str(line_width) + 's '
                    '%(file)s%(plain)s'
                    '%(funcemph)s%(function)s%(plain)s\n')

        # Stack frames:
        for i, (file, line, function, text) in enumerate(extracted_tb):
            # extract_tb() doesn't return Unicode, so we have to guess at the
            # encoding. We guess utf-8. Use utf-8, everybody.
            yield (format_shortcut(editor, file, line, function) +
                   ('    %s\n' % (text or '').decode('utf-8')))

    # Exception:
    if exc_type is SyntaxError:
        # Format a SyntaxError to look like our other traceback lines.
        # SyntaxErrors have a format different from other errors and include a
        # file path which looks out of place in our newly highlit, editor-
        # shortcutted world.
        exc_lines = [format_shortcut(editor, exc_value.filename, exc_value.lineno)] + \
                     format_exception_only(SyntaxError, exc_value)[1:]
    else:
        exc_lines = format_exception_only(exc_type, exc_value)
    yield ''.join(exc_lines)


# Adapted from unittest:

def extract_relevant_tb(tb, exctype, is_test_failure):
    """Return extracted traceback frames that aren't unittest ones.

    This used to be _exc_info_to_string().

    """
    # Skip test runner traceback levels:
    while tb and _is_unittest_frame(tb):
        tb = tb.tb_next
    if is_test_failure:
        # Skip assert*() traceback levels:
        length = _count_relevant_tb_levels(tb)
        return extract_tb(tb, length)
    return extract_tb(tb)


def _is_unittest_frame(tb):
    """Return whether the given frame is something other than a unittest one."""
    return '__unittest' in tb.tb_frame.f_globals


def _count_relevant_tb_levels(tb):
    """Return the number of frames in ``tb`` before all that's left is unittest frames.

    Unlike its namesake in unittest, this doesn't bail out as soon as it hits a
    unittest frame, which means we don't bail out as soon as somebody uses the
    mock library, which defines ``__unittest``.

    """
    length = contiguous_unittest_frames = 0
    while tb:
        length += 1
        if _is_unittest_frame(tb):
            contiguous_unittest_frames += 1
        else:
            contiguous_unittest_frames = 0
        tb = tb.tb_next
    return length - contiguous_unittest_frames
