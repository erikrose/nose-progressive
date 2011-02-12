from curses import tigetnum, tigetstr, setupterm, tparm
import inspect
import logging
import os
from traceback import format_list, extract_tb
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
        setupterm(None, stream.fileno())  # Make setupterm() work even when -s is passed. TODO: Don't do this if self.stream isn't a terminal. Use os.isatty(self.stream.fileno()). If it isn't, perhaps replace the ShyProgressBar with a dummy object.
        self.bar = ProgressBar()
        return DummyStream()

    def printError(self, kind, err, test):
        _, _, tb = err
        extracted_tb = extract_tb(tb)
        formatted_err = ''.join(format_list(extracted_tb))
        # TODO: Format the tb ourselves and eliminate the space-wasting
        # "Traceback (most recent..." line to make up for the extra pathname
        # line.
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
                line_num = extracted_tb[-1][1]
                writeln(' ' * len(kind) +
                        '  %s +%s' % (relative_source_path(file_name), line_num))

            write(tigetstr('sgr0'))
            self.stream.write(formatted_err)

    def printErrors(self):
        # The current summary doesn't begin with a \n.
        with ShyProgressBar(self.stream, self.bar):
            self.stream.writeln()

    def finalize(self, result):
        """Print counts of tests run."""
        types = ['test', 'failure', 'error', 'skip']
        values = [self.testsRun, len(result.failures), len(result.errors), len(result.skipped)]
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
    def __init__(self):
        width = tigetnum('cols')
        self.last = ' ' * width

    def get(self, test, number):
        number = str(number)
        test_path = python_path(test.test) + '.' + test.test._testMethodName
        width = tigetnum('cols')
        cols_for_path = width - len(number) - 2  # 2 spaces between path and number
        if len(test_path) > cols_for_path:
            test_path = test_path[len(test_path) - cols_for_path:]
        else:
            test_path += ' ' * (cols_for_path - len(test_path))
        self.last = tigetstr('bold') + test_path + '  ' + number + tigetstr('sgr0')
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
        # Doing this each time gives us a hope of adjusting if people resize their terminals during test runs:
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
