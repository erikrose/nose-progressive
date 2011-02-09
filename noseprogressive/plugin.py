import inspect
import logging
import os
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

        stream.__class__ = StreamWithProgress  # in the hope that this will keep other users of the stream from wrecking our progress indicator
        self.stream = stream
        return DevNullStream()

    def getDescription(self, test):
        return nice_test_address(test)

    def printError(self, kind, err, test):
        formatted_err = format_exception(*err)
        writeln = self.stream.writeln
        writeln()
        writeln('=' * 70)
        writeln('%s: %s' % (kind, self.getDescription(test)))
        writeln('-' * 70)
        writeln(''.join(formatted_err))
        self.stream.flush()

    def printErrors(self):
        # The current summary doesn't begin with a \n.
        self.stream.writeln()

    # TODO: Override printSummary() to add footer.

    def addError(self, test, err):
        exc, val, tb = err
        if isinstance(exc, SkipTest):
            self.stream.writeln()
            self.stream.writeln('SKIP: %s' % nice_test_address(test))
        else:
            self.printError('ERROR', err, test)

    def addFailure(self, test, err):
        self.printError('FAIL', err, test)

    def addSkip(self, test, reason):
        # Only in 2.7+
        self.stream.writeln()
        self.stream.writeln('SKIP: %s' % nice_test_address(test))

    def addSuccess(self, test):
        self.stream.writeln(get_context(test.test) + '.' + test.test._testMethodName)
        self.stream.flush()


class StreamWithProgress(_WritelnDecorator):
    # TODO: Think about doing this as a "with" statement.
    def writeln(self, arg=None):
        # TODO: Erase progress indicator.
        super(StreamWithProgress, self).writeln(arg)
        # TODO: Redraw progress indicator.


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
