"""Fancy traceback formatting"""

import os
from traceback import format_exception_only

from nose.util import src

from noseprogressive.terminal import height_and_width, Terminal
from noseprogressive.utils import human_path


def format_traceback(extracted_tb,
                     exc_type,
                     exc_value,
                     cwd='',
                     frame_to_emphasize=None,
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
                        function=None,
                        emphasizer='',
                        deemphasizer=''):
        """Return a pretty-printed editor shortcut."""
        return template % dict(editor=editor,
                               line=line,
                               file=file,
                               function=('  # ' + function) if function else '',
                               emph=emphasizer,
                               deemph=deemphasizer,
                               funcemph=term.color(function_color),
                               # Underline is also nice and doesn't make us
                               # worry about appearance on different background
                               # colors.
                               plain=term.normal,
                               fade=term.color(dim_color) + term.bold)

    if not term:
        term = Terminal()

    # TODO: Relativize paths by default, but provide a flag to keep them
    # absolute for pasting into editors and other terminal windows.
    # TODO: Test with SyntaxErrors in the test frame. Make sure the test
    # frame gets emboldened.

    # Shorten file paths:
    for i, (file, line, function, text) in enumerate(extracted_tb):
        extracted_tb[i] = human_path(src(file), cwd), line, function, text

    line_width = len(str(max(the_line for _, the_line, _, _ in extracted_tb)))
    editor = os.environ.get('EDITOR', 'vi')

    template = ('  %(fade)s%(emph)s%(editor)s +%(line)-{line_width}s '
                '%(file)s%(plain)s%(emph)s'
                '%(funcemph)s%(function)s%(plain)s%(emph)s%(deemph)s\n').format(line_width=line_width)

    # Stack frames:
    for i, (file, line, function, text) in enumerate(extracted_tb):
        if i == frame_to_emphasize:
            emph, deemph = term.bg_color(highlight_color), term.normal
        else:
            emph, deemph = '', ''
        yield (format_shortcut(editor, file, line, function, emph, deemph) +
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
