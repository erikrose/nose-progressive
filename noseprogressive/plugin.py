from curses import tigetnum, tigetstr, setupterm, tparm
import inspect
import logging
import os
import random
from time import sleep
from traceback import format_exception
import unittest
from unittest import TestCase, _WritelnDecorator

from nose.plugins import Plugin
from nose.exc import SkipTest
from nose.case import FunctionTestCase
from nose.util import test_address

log = logging.getLogger('nose.plugins.ProgressivePlugin')

class ProgressivePlugin(Plugin):
    """Nose plugin which prioritizes the important information"""
    name = 'progressive'

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
        class DevNullStream(object):
            writeln = flush = write = lambda self, *args: None

        self.stream = stream
        setupterm()  # TODO: Don't do this if self.stream isn't a terminal. Use os.isatty(self.stream.fileno()). If it isn't, perhaps replace the ShyProgressBar with a dummy object.
        return DevNullStream()

    def getDescription(self, test):
        return nice_test_address(test)

    def printError(self, kind, err, test):
        formatted_err = format_exception(*err)
        with ShyProgressBar(self.stream, test):
            writeln = self.stream.writeln
            writeln()
            writeln('=' * 70)
            writeln('%s: %s' % (kind, self.getDescription(test)))
            writeln('-' * 70)
            writeln(''.join(formatted_err))

    def printErrors(self):
        # The current summary doesn't begin with a \n.
        with ShyProgressBar(self.stream, test):
            self.stream.writeln()

    # TODO: Override printSummary() to add footer.

    def addError(self, test, err):
        exc, val, tb = err
        with ShyProgressBar(self.stream, test):
            if isinstance(exc, SkipTest):
                self.stream.writeln()
                self.stream.writeln('SKIP: %s' % nice_test_address(test))
            else:
                self.printError('ERROR', err, test)

    def addFailure(self, test, err):
        self.printError('FAIL', err, test)

    def addSkip(self, test, reason):
        # Only in 2.7+
        with ShyProgressBar(self.stream, test):
            self.stream.writeln()
            self.stream.writeln('SKIP: %s' % nice_test_address(test))

    def addSuccess(self, test):
        with AtProgressBar(self.stream):
            self.stream.write(progress_bar(test))


def progress_bar(test):
    REV = tigetstr('rev')
    return tigetstr('el') + REV + get_context(test.test) + '.' + test.test._testMethodName + REV


class AtProgressBar(object):
    def __init__(self, stream):
        self.stream = stream

    def __enter__(self):
        """Save position and move to progress bar, col 1."""
        self.stream.write(tigetstr('sc'))  # save position
        width, height = tigetnum('cols'), tigetnum('lines')
        self.stream.write(tparm(tigetstr('cup'), height, 0))
    
    def __exit__(self, type, value, tb):
        self.stream.write(tigetstr('rc'))  # restore position


class ShyProgressBar(object):
    """Context manager that implements a progress bar that gets out of the way
    """

    def __init__(self, stream, test):
        self.stream = stream
        self.test = test

    def __enter__(self):
        """Erase the progress bar so bits of disembodied progress bar don't get scrolled up the terminal."""
        # My terminal has no status line, so we make one manually.
        # Doing this each time gives us a hope of adjusting if people resize their terminals during test runs:
        with AtProgressBar(self.stream):
            self.stream.write(tigetstr('el'))  # erase to EOL
        self.stream.flush()

    def __exit__(self, type, value, tb):
        """Redraw the progress bar at the bottom of the terminal."""
        with AtProgressBar(self.stream):
            self.stream.write(progress_bar(self.test))
        self.stream.flush()


def nice_test_address(test):
    addr = test_address(test)
    if addr is None:
        return '??'
    path, module, test_path = addr
    path = nice_path(path)
    if test_path is None:
        return path
    return '%s:%s' % (path, test_path)

nice_test_address.__test__ = False # Not a test for Nose


def get_context(test):
    # TODO: Can't we just use test.address()?
    if isinstance(test, FunctionTestCase):
        context = nice_path(inspect.getfile(inspect.getmodule(test.test)))
    elif isinstance(test, TestCase):
        context = '%s:%s' % (nice_path(inspect.getfile(test.__class__)),
                             test.__class__.__name__)
    else:
        raise NotImplemented('Unsure how to get context from: %r' % test)

    return context


def nice_path(path):
    path = os.path.abspath(path)
    if path.startswith(os.getcwd()):
        path = path.replace(os.getcwd(), '')[1:] # shorten and remove slash
    if path.endswith('.pyc'):
        path = path[0:-1]
    return path
