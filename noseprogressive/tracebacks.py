"""Fancy traceback formatting"""

import os

from nose.util import src

from noseprogressive.terminal import height_and_width, Terminal
from noseprogressive.utils import human_path


def format_traceback(extracted_tb, cwd='', frame_to_emphasize=None, term=None):
    """Return an iterable of formatted traceback frames, rather like traceback.format_list().

    Format things more compactly than the stock formatter, and make every
    frame an editor shortcut. Emphasize the line representing the stack frame
    of the test, if you pass in the index of that frameHoly.

    """
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

    for i, (file, line, function, text) in enumerate(extracted_tb):
        if i == frame_to_emphasize:
            emph, deemph = term.bg_color(15), term.normal
        else:
            emph, deemph = '', ''
        yield (format_shortcut(term, file, line, function, line_width, emph, deemph) +
               ('    %s\n' % (text or '')))


def format_shortcut(term, file, line, function=None, line_number_width=0, emphasizer='', deemphasizer=''):
    """Return a pretty-printed editor shortcut."""
    template = ('  %(fade)s%(emph)s%(editor)s +%(line)-{line_width}s '
                '%(file)s%(plain)s%(emph)s'
                '%(funcemph)s%(function)s%(plain)s%(emph)s%(deemph)s\n').format(line_width=line_number_width)
    return template % dict(editor=os.environ.get('EDITOR', 'vi'),
                           line=line,
                           file=file,
                           function=('  # ' + function) if function else '',
                           emph=emphasizer,
                           deemph=deemphasizer,
                           funcemph=term.color(12),  # Underline is also nice and doesn't make us worry about appearance on different background colors.
                           plain=term.normal,
                           fade=term.color(8) + term.bold)
