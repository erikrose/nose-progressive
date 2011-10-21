"""Fancy traceback formatting"""

import os
from traceback import extract_tb, format_exception_only

from nose.util import src

from noseprogressive.terminal import Terminal
from noseprogressive.utils import human_path


def format_traceback(extracted_tb,
                     exc_type,
                     exc_value,
                     cwd='',
                     term=None,
                     highlight_color=15,
                     function_color=12,
                     dim_color=8):
    """Return an iterable of formatted traceback frames.

    Also include a pseudo-frame at the end representing the exception itself.

    Format things more compactly than the stock formatter, and make every
    frame an editor shortcut. Emphasize the line representing the stack frame
    of the test, if you pass in the index of that frameHoly.

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

    # TODO: Test with SyntaxErrors in the test frame. Make sure the test
    # frame gets emboldened.

    # Shorten file paths:
    for i, (file, line, function, text) in enumerate(extracted_tb):
        extracted_tb[i] = human_path(src(file), cwd), line, function, text

    line_width = len(str(max(the_line for _, the_line, _, _ in extracted_tb)))
    editor = os.environ.get('EDITOR', 'vi')

    template = ('  %(fade)s%(editor)s +%(line)-{line_width}s '
                '%(file)s%(plain)s'
                '%(funcemph)s%(function)s%(plain)s\n').format(line_width=line_width)

    # Stack frames:
    for i, (file, line, function, text) in enumerate(extracted_tb):
        yield (format_shortcut(editor, file, line, function) +
               ('    %s\n' % (text or '')))

    # Exception:
    if exc_type is SyntaxError:
        # Format a syntaxError to look like our other traceback lines.
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
    while tb and _is_relevant_tb_level(tb):
        tb = tb.tb_next
    if is_test_failure:
        # Skip assert*() traceback levels:
        length = _count_relevant_tb_levels(tb)
        return extract_tb(tb, length)
    return extract_tb(tb)


def _is_relevant_tb_level(tb):
    return '__unittest' in tb.tb_frame.f_globals


def _count_relevant_tb_levels(tb):
    length = 0
    while tb and not _is_relevant_tb_level(tb):
        length += 1
        tb = tb.tb_next
    return length
