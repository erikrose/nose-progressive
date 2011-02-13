from curses import tigetnum, tigetstr, setupterm, tparm
import inspect
from itertools import cycle
import logging
import os
from traceback import format_list, extract_tb, format_exception_only
from unittest import TestCase

from nose.plugins import Plugin
from nose.exc import SkipTest
from nose.case import FunctionTestCase
from nose.util import test_address


log = logging.getLogger('nose.plugins.ProgressivePlugin')


class ProgressivePlugin(Plugin):
    """Nose plugin which prioritizes the important information"""
    name = 'progressive'
    testsRun = 0

    # TODO: Decrease score so we run early, and monkeypatch stderr in __init__.
    # See if that works.

    def options(self, parser, env=os.environ):
        super(ProgressivePlugin, self).options(parser, env=env)
        self.parser = parser

    def configure(self, options, conf):
        super(ProgressivePlugin, self).configure(options, conf)
        if self.enabled:
            self.cmd_options = options
            self.config = conf

    def setOutputStream(self, stream):
        """Steal the stream, and return a mock one for everybody else to shut them up."""
        class DummyStream(object):
            writeln = flush = write = lambda self, *args: None

        self.stream = stream
        # Explicit args make setupterm() work even when -s is passed:
        setupterm(None, stream.fileno())
        # TODO: Don't call setupterm() if self.stream isn't a terminal. Use
        # os.isatty(self.stream.fileno()). If it isn't, perhaps replace the
        # ShyProgressBar with a dummy object.

        return DummyStream()

    def prepareTest(self, test):
        """Init the progress bar, and tell it how many tests there are."""
        # Not really clear from the docs whether this always gets called in
        # every plugin or whether another plugin can prevent this from getting
        # called by returning something. If the latter, we'll be surprised when
        # self.bar doesn't exist.
        self.bar = ProgressBar(test.countTestCases())

    def printError(self, kind, err, test):
        """Output a human-readable error report to the stream.

        kind -- the (string) type of incident the precipitated this call
        err -- exc_info()-style traceback triple
        test -- the test that precipitated this call

        """
        # Don't bind third item to a local var; that can create circular refs
        # which are expensive to collect. See the sys.exc_info() docs.
        exception_type, exception_value = err[:2]
        extracted_tb = extract_tb(err[2])
        formatted_err = ''.join(format_list(extracted_tb))
        # TODO: Canonicalize the path to remove /kitsune/../kitsune nonsense.
        # Don't relativize, though, as that hurts the ability to paste into
        # running editors.
        with ShyProgressBar(self.stream, self.bar):
            writeln = self.stream.writeln
            write = self.stream.write
            writeln()
            write(tigetstr('bold'))
            writeln('%s: %s' % (kind, python_path(test)))

            # File name and line num in a format vi can take:
            address = test.address()
            if address:
                file_name = address[0]
                if file_name:
                    line_num = extracted_tb[-1][1]
                    writeln(' ' * len(kind) +
                            '  %s +%s' % (relative_source_path(file_name), line_num))

            write(tigetstr('sgr0'))

            # Traceback:
            self.stream.write(formatted_err)

            # Exception:
            self.stream.write(''.join(format_exception_only(exception_type, exception_value)))


    def printErrors(self):
        # The current summary doesn't begin with a \n.
        with ShyProgressBar(self.stream, self.bar):
            self.stream.writeln()

    def finalize(self, result):
        """Print counts of tests run."""
        types = ['test', 'failure', 'error']
        values = [self.testsRun, len(result.failures), len(result.errors)]
        if hasattr(result, 'skipped'):  # Absent if --no-skip is passed
            types.append('skip')
            values.append(len(result.skipped))
        msg = ', '.join('%s %s%s' % (v, t, 's' if v != 1 else '')
                        for t, v in zip(types, values))

        # Erase progress bar. Bash doesn't clear the whole line when printing
        # the prompt, leaving a piece of the bar.
        with AtProgressBar(self.stream):
            self.stream.write(tigetstr('el'))
        self.stream.writeln('\n' + msg)

    def startTest(self, test):
        # Overriding this seems to prevent TextTestRunner from running its, so
        # we have to keep track of the test count ourselves.
        self.testsRun += 1
        with AtProgressBar(self.stream):
            self.stream.write(self.bar.get(test, self.testsRun))

    def addError(self, test, err):
        exc, val, tb = err
        with ShyProgressBar(self.stream, self.bar):
            if isinstance(exc, SkipTest):
                self.stream.writeln()
                self.stream.writeln('SKIP: %s' % nose_selector(test))
            else:
                self.printError('ERROR', err, test)

    def addFailure(self, test, err):
        self.printError('FAIL', err, test)

    def addSkip(self, test, reason):
        # Only in 2.7+
        # TODO: This never gets called, at least in 2.6.
        with ShyProgressBar(self.stream, self.bar):
            self.stream.writeln()
            self.stream.writeln('SKIP: %s' % nose_selector(test))


class ProgressBar(object):
    SPINNER_CHARS = r'/-\|'

    def __init__(self, max):
        """max is the highest value I will attain. Must be >0."""
        self.last = ''  # The contents of the previous progress line printed
        self.max = max
        self.spinner = cycle(self.SPINNER_CHARS)

    def get(self, test, number):
        """Return updated content for the progress bar.

        At the moment, the graph takes a fixed width, and the test identifier
        takes the rest of the row, truncated from the left to fit.

        test -- the test being run
        number -- how many tests have been run so far, including this one

        """
        # TODO: Play nicely with absurdly narrow terminals.

        # Figure out graph:
        # We cheat a bit and dedicate extra column to the spinner to make the
        # logic simple, so the graph is just sliiiightly misproportional.
        GRAPH_WIDTH = 14
        num_markers = int(round(float(number) / self.max * GRAPH_WIDTH))
        # If there are any markers, replace the last one with the spinner.
        # Otherwise, have just a spinner:
        markers = '=' * (num_markers - 1) + self.spinner.next()
        graph = '[%s%s]' % (markers,
                            ' ' * (GRAPH_WIDTH - len(markers)))

        # Figure out the test identifier portion:
        test_path = python_path(test.test) + '.' + test.test._testMethodName
        width = tigetnum('cols')
        cols_for_path = width - len(graph) - 2  # 2 spaces between path & graph
        if len(test_path) > cols_for_path:
            test_path = test_path[len(test_path) - cols_for_path:]
        else:
            test_path += ' ' * (cols_for_path - len(test_path))
        
        # Put them together, and let simmer:
        self.last = tigetstr('bold') + test_path + '  ' + graph + tigetstr('sgr0')
        return self.last


class AtProgressBar(object):
    """Context manager which goes to the progress bar line on entry and goes back to where it was on exit"""

    def __init__(self, stream):
        self.stream = stream

    def __enter__(self):
        """Save position and move to progress bar, col 1."""
        self.stream.write(tigetstr('sc'))  # save position
        height = tigetnum('lines')
        self.stream.write(tparm(tigetstr('cup'), height, 0))

    def __exit__(self, type, value, tb):
        self.stream.write(tigetstr('rc'))  # restore position


class ShyProgressBar(object):
    """Context manager that implements a progress bar that gets out of the way"""

    def __init__(self, stream, bar):
        self.stream = stream
        self.bar = bar

    def __enter__(self):
        """Erase the progress bar so bits of disembodied progress bar don't get scrolled up the terminal."""
        # My terminal has no status line, so we make one manually.
        with AtProgressBar(self.stream):
            self.stream.write(tigetstr('el'))  # erase to EOL
        self.stream.flush()

    def __exit__(self, type, value, tb):
        """Do nothing; the bar will come back at the top of the next test, which is imminent."""
        # This isn't really necessary unless we monkeypatch stderr; the next
        # test is about to start and will redraw the bar.
        with AtProgressBar(self.stream):
            self.stream.write(self.bar.last)
        self.stream.flush()


def nose_selector(test):
    """Return the string you can pass to nose to run `test`."""
    file, module, rest = test_address(test)
    file = relative_source_path(file)
    if rest:
        return '%s:%s' % (file, rest)
    else:
        return file


def python_path(test):
    address = test_address(test)
    if address:
        file, module, rest = address
    else:
        return 'Unknown test'

    if rest:
        return '%s:%s' % (module, rest)
    else:
        return module


def relative_source_path(path):
    """Return a relative filesystem path to the source file of the possibly-compiled module at the given path."""
    path = os.path.abspath(path)
    cwd = os.getcwd()
    if path.startswith(cwd):
        path = path[len(cwd) + 1:]  # Make path relative. Remove leading slash.
    if path.endswith('.pyc'):
        path = path[:-1]
    return path
