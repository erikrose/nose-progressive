from collections import defaultdict
from curses import tigetstr, setupterm, tparm
from os import isatty
from traceback import format_list, extract_tb, format_exception_only
from unittest import TestResult

from nose.exc import SkipTest
from nose.util import src

from noseprogressive.bar import ProgressBar
from noseprogressive.utils import nose_selector, human_path, frame_of_test


class ProgressiveResult(TestResult):
    """Test result which updates a progress bar instead of printing dots

    Nose's ResultProxy will wrap it, and other plugins can still print
    stuff---but without smashing into my progress bar, care of my Plugin's
    stderr/out wrapping.

    """
    def __init__(self, cwd, totalTests, stream):
        super(ProgressiveResult, self).__init__()
        self._cwd = cwd
        self.stream = stream
        self._codes = self._terminalCodes(stream)

        # 1 in case test counting failed and returned 0
        self.bar = ProgressBar(stream, totalTests or 1, self._codes)
        self.bar.stream = stream

        # Dammit, nose is expecting these, even though they're not part of the contract:
        self.showAll = self.dots = False

    def _terminalCodes(self, stream):
        """Return a hash of termcap codes and values for the terminal `stream`.

        If `stream` is not a terminal, return empty values so you can pipe this
        to a file without making a mess of it. (I'm not sure why you would want
        to do that; this is mostly in place to make the Progressive's test
        suite run.)

        """
        capabilities = ['bold', 'sc', 'rc', 'sgr0', 'el']
        if hasattr(stream, 'fileno') and isatty(stream.fileno()):
            # Explicit args make setupterm() work even when -s is passed:
            setupterm(None, stream.fileno())  # so things like tigetstr() work
            codes = dict((x, tigetstr(x)) for x in capabilities)
            cup = tigetstr('cup')
            codes['cup'] = lambda line, column: tparm(cup, line, column)
        else:
            # If you're crazy enough to pipe this to a file or something, don't
            # output terminal codes:
            codes = defaultdict(lambda: '', cup=lambda line, column: '')
        return codes

    def startTest(self, test):
        """Update the progress bar."""
        super(ProgressiveResult, self).startTest(test)
        self.bar.update(test, self.testsRun)

    def _printError(self, kind, err, test):
        """Output a human-readable error report to the stream.

        kind -- the (string) type of incident the precipitated this call
        err -- exc_info()-style traceback triple
        test -- the test that precipitated this call

        """
        # Don't bind third item to a local var; that can create circular refs
        # which are expensive to collect. See the sys.exc_info() docs.
        exception_type, exception_value = err[:2]
        extracted_tb = extract_tb(err[2])
        formatted_traceback = ''.join(format_list(extracted_tb))
        # TODO: Canonicalize the path to remove /kitsune/../kitsune nonsense.
        # Don't relativize, though, as that hurts the ability to paste into
        # running editors.
        writeln = self.stream.writeln
        write = self.stream.write
        with self.bar.dodging():
            writeln('\n' + self._codes['bold'] +
                    '%s: %s' % (kind, nose_selector(test)))

            # File name and line num in a format vi can take:
            address = test.address()
            if address:  # None if no such callable found. No sense trying to
                         # find the test frame if there's no such thing.
                file, line = frame_of_test(address, extracted_tb)[:2]
                writeln(' ' * len(kind) + '  +%s %s' %
                        (line, human_path(src(file), self._cwd)))

            write(self._codes['sgr0'])  # end bold

            # Traceback:
            write(formatted_traceback)

            # Exception:
            write(''.join(format_exception_only(exception_type,
                                                exception_value)))

    def addError(self, test, err):
        super(ProgressiveResult, self).addError(test, err)
        exc, val, tb = err
        with self.bar.dodging():
            if isinstance(exc, SkipTest):
                self.stream.writeln()
                self.stream.writeln('SKIP: %s' % nose_selector(test))
            else:
                self._printError('ERROR', err, test)

    def addFailure(self, test, err):
        super(ProgressiveResult, self).addFailure(test, err)
        self._printError('FAIL', err, test)

    def printErrorsForReal(self, timeTaken):
        """As a final summary, print number of tests, broken down by result."""
        def renderResultType(type, number):
            """Return a rendering like '2 failures', given a type like 'failure' and a number of them."""
            ret = '%s %s%s' % (number, type, 's' if number != 1 else '')
            if type in ['failure', 'error'] and number:
                ret = self._codes['bold'] + ret + self._codes['sgr0']
            return ret

        types = ['test', 'failure', 'error']
        values = [self.testsRun, len(self.failures), len(self.errors)]
        if hasattr(self, 'skipped'):  # Absent if --no-skip is passed
            types.append('skip')
            values.append(len(self.skipped))
        msg = (', '.join(renderResultType(t, v) for t, v in zip(types, values)) +
               ' in %.1fs' % timeTaken)

        # Erase progress bar. Bash doesn't clear the whole line when printing
        # the prompt, leaving a piece of the bar. Also, the prompt may not be
        # at the bottom of the terminal.
        self.bar.erase()
        self.stream.writeln()
        if self.wasSuccessful():
            self.stream.write('OK!  ')
        self.stream.writeln(msg)
