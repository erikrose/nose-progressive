"""Fancy traceback formatting"""

import os

from nose.util import src

from noseprogressive.terminal import height_and_width, Terminal
from noseprogressive.utils import human_path


def format_traceback(extracted_tb, cwd='', frame_to_emphasize=None, term=None):
    """Return an iterable of formatted traceback frames, rather like traceback.format_list().

    Format things more compactly than the stock formatter, and make every
    line an editor shortcut. Embolden the line representing the stack frame
    of the test, if we can figure that out based on `address`.

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

    # Column widths:
    line_width = len(str(max(the_line for _, the_line, _, _ in extracted_tb)))
    file_width = max(len(f) for f, _, _, _ in extracted_tb)
    terminal_width = height_and_width()[1]

    template = ('  %(fade)s%(emph)s{editor} +%(line)-{line_width}s %(file)s  %(plain)s%(emph)s%(funcemph)s# %(function)s%(plain)s%(emph)s%(deemph)s\n'
                '    %(text)s\n'.format(editor=os.environ.get('EDITOR', 'vi'),
                                  line_width=line_width))

    for i, (file, line, function, text) in enumerate(extracted_tb):
        if i == frame_to_emphasize:
            emph, deemph = term.bg_color(15), term.normal
        else:
            emph, deemph = '', ''
        yield template % dict(line=line,
                              file=file,
                              function=function,
                              text=text or '',
                              emph=emph,
                              deemph=deemph,
                              funcemph=term.color(12),  # Underline is also nice and doesn't make us worry about appearance on different background colors.
                              plain=term.normal,
                              fade=term.color(8) + term.bold)
