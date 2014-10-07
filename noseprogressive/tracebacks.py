"""Fancy traceback formatting"""

import os
from sys import version_info

from traceback import extract_tb, format_exception_only

from blessings import Terminal
from nose.util import src

from noseprogressive.utils import human_path


DEFAULT_EDITOR_SHORTCUT_TEMPLATE = (u'  {dim_format}{editor} '
                                     '+{line_number:<{line_number_max_width}} '
                                     '{path}{normal}'
                                     '{function_format}{hash_if_function}'
                                     '{function}{normal}')


def format_traceback(extracted_tb,
                     exc_type,
                     exc_value,
                     cwd='',
                     term=None,
                     function_color=12,
                     dim_color=8,
                     editor='vi',
                     template=DEFAULT_EDITOR_SHORTCUT_TEMPLATE):
    """Return an iterable of formatted Unicode traceback frames.

    Also include a pseudo-frame at the end representing the exception itself.

    Format things more compactly than the stock formatter, and make every
    frame an editor shortcut.

    """
    def format_shortcut(editor,
                        path,
                        line_number,
                        function=None):
        """Return a pretty-printed editor shortcut."""
        return template.format(editor=editor,
                               line_number=line_number,
                               path=path,
                               function=function or u'',
                               hash_if_function=u'  # ' if function else u'',
                               function_format=term.color(function_color),
                               # Underline is also nice and doesn't make us
                               # worry about appearance on different background
                               # colors.
                               normal=term.normal,
                               dim_format=term.color(dim_color) + term.bold,
                               line_number_max_width=line_number_max_width,
                               term=term)

    template += '\n'  # Newlines are awkward to express on the command line.
    extracted_tb = _unicode_decode_extracted_tb(extracted_tb)
    if not term:
        term = Terminal()

    if extracted_tb:
        # Shorten file paths:
        for i, (file, line_number, function, text) in enumerate(extracted_tb):
            extracted_tb[i] = human_path(src(file), cwd), line_number, function, text

        line_number_max_width = len(unicode(max(the_line for _, the_line, _, _ in extracted_tb)))

        # Stack frames:
        for i, (path, line_number, function, text) in enumerate(extracted_tb):
            text = (text and text.strip()) or u''

            yield (format_shortcut(editor, path, line_number, function) +
                   (u'    %s\n' % text))

    # Exception:
    if exc_type is SyntaxError:
        # Format a SyntaxError to look like our other traceback lines.
        # SyntaxErrors have a format different from other errors and include a
        # file path which looks out of place in our newly highlit, editor-
        # shortcutted world.
        exc_lines = [format_shortcut(editor, exc_value.filename, exc_value.lineno)]
        formatted_exception = format_exception_only(SyntaxError, exc_value)[1:]
    else:
        exc_lines = []
        formatted_exception = format_exception_only(exc_type, exc_value)
    exc_lines.extend([_decode(f) for f in formatted_exception])
    yield u''.join(exc_lines)


# Adapted from unittest:

def extract_relevant_tb(tb, exctype, is_test_failure):
    """Return extracted traceback frame 4-tuples that aren't unittest ones.

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


def _decode(string):
    """Decode a string as if it were UTF-8, swallowing errors. Turn Nones into
    "None", which is more helpful than crashing.

    In Python 2, extract_tb() returns simple strings. We arbitrarily guess that
    UTF-8 is the encoding and use "replace" mode for undecodable chars. I'm
    guessing that in Python 3 we've come to our senses and everything's
    Unicode. We'll see when we add Python 3 to the tox config.

    """
    if string is None:
        return 'None'
    return string if isinstance(string, unicode) else string.decode('utf-8', 'replace')


def _unicode_decode_extracted_tb(extracted_tb):
    """Return a traceback with the string elements translated into Unicode."""
    return [(_decode(file), line_number, _decode(function), _decode(text))
            for file, line_number, function, text in extracted_tb]


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
