from curses import tigetnum, tigetstr, setupterm, tparm
from fcntl import ioctl
from functools import partial
from itertools import cycle
import os
from signal import signal, SIGWINCH
import struct
from termios import TIOCGWINSZ
from traceback import format_list, extract_tb, format_exception_only

from nose.plugins import Plugin
from nose.exc import SkipTest
from nose.util import test_address


class ProgressivePlugin(Plugin):
    """Nose plugin which prioritizes the important information"""
    name = 'progressive'
    testsRun = 0
    _totalTests = 0

    # TODO: Decrease score so we run early, and monkeypatch stderr in __init__.
    # See if that works.

    def setOutputStream(self, stream):
        """Steal the stream, and return a mock one for everybody else to shut them up."""
        class DummyStream(object):
            writeln = flush = write = lambda self, *args: None

        # 1 in case test counting failed and returned 0
        self.bar = ProgressBar(stream, self._totalTests or 1)
        
        self.stream = self.bar.stream = stream
        # Explicit args make setupterm() work even when -s is passed:
        setupterm(None, stream.fileno())  # so things like tigetstr() work
        # TODO: Don't call setupterm() if self.stream isn't a terminal. Use
        # os.isatty(self.stream.fileno()). If it isn't, perhaps replace the
        # ShyProgressBar with a dummy object.

        return DummyStream()

    def prepareTest(self, test):
        """Init the progress bar, and tell it how many tests there are."""
        # TODO: It's not documented, but another plugin can prevent this from
        # getting called by returning something. If that happens latter, we'll
        # be surprised when self.bar doesn't exist.
        
        # We can't just call test.countTestCases(), because that exhausts the
        # iterator, and then the actual test runner doesn't find any tests. We
        # could tee the generator, but that generator is full of other
        # generators, so it's complicated and would use RAM proportional with
        # the number of tests. So instead, we re-run the discovery process
        # ourselves.
#         tests_for_preflight, test._tests = tee(test._tests)
# 
#         total = 0
#         for t in tests_for_preflight:
#             total += t.countTestCases()

        # Okay, re-running everything and getting the exact same options is
        # quite hard: nose isn't written such that I can easily set everything
        # up and then hook in and get the info I need without firing off the
        # test runs in its entirety. Let's blow the RAM.
        # OTOH, I can call nose.core.collector() and get the number out of .suite.countTestCases(). However, the options used by collector() don't always reflect the options the in-progress run is using. For example, django-nose calls TestProgram itself and passes in a customized argv and plugin list. collector() doesn't even seem to see argv, at least under django-nose. Thus, we pretty much need to start from where we are and tee generators or something.
        
        # Phase 1: tee the generators, and replace the sources with one of the tees:
        
        # Phase 2: Take one of the tees, and traverse/iterator through it, counting things.
        
        # So if each thing is a TestSuite subclass, replace it with thing._tests.
        # If it's a unittest.TestCase subclass, leave it alone.
        # [Then,] If it's a generator (callable), replace it with list(thing).
        
        
        #self._totalTests = 2
#         
#         return test

    def prepareTestLoader(self, loader):
        """Insert ourselves into loader calls to count tests.
        
        The top-level loader call often returns lazy results. This is a
        problem, as we would destroy them by iterating over them to count the
        test cases. Monkeypatch the top-level loader call to do the load twice:
        once for the actual test running and again to yield something we can
        iterate over to do the count.
        
        """
        def capture_suite(orig_method, *args, **kwargs):
            """Intercept calls to the loader before they get lazy.

            Re-execute them to grab a copy of the possibly lazy results, and
            count the tests therein.

            """
            suite = orig_method(*args, **kwargs)
            self._totalTests += orig_method(*args, **kwargs).countTestCases()
            return suite
        
        if hasattr(loader, 'loadTestsFromNames'):
            loader.loadTestsFromNames = partial(capture_suite,
                                                loader.loadTestsFromNames)
        return loader

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
        with self.bar.dodging():
            writeln = self.stream.writeln
            write = self.stream.write
            writeln()
            write(tigetstr('bold'))
            writeln('%s: %s' % (kind, nose_selector(test)))

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
        with self.bar.dodging():
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
        self.bar.erase()
        self.stream.writeln('\n' + msg)

    def startTest(self, test):
        # Overriding this seems to prevent TextTestRunner from running its, so
        # we have to keep track of the test count ourselves.
        self.testsRun += 1
        self.bar.update(test, self.testsRun)

    def addError(self, test, err):
        exc, val, tb = err
        with self.bar.dodging():
            if isinstance(exc, SkipTest):
                self.stream.writeln()
                self.stream.writeln('SKIP: %s' % nose_selector(test))
            else:
                self.printError('ERROR', err, test)

    def addFailure(self, test, err):
        self.printError('FAIL', err, test)


class ProgressBar(object):
    SPINNER_CHARS = r'/-\|'

    def __init__(self, stream, max):
        """max is the highest value I will attain. Must be >0."""
        self.stream = stream
        self.last = ''  # The contents of the previous progress line printed
        self.max = max
        self._spinner = cycle(self.SPINNER_CHARS)
        self._measure_terminal()
        signal(SIGWINCH, self._handle_winch)

    def _measure_terminal(self):
        self.lines, self.cols = \
            struct.unpack('hhhh', ioctl(0, TIOCGWINSZ, '\000' * 8))[0:2]

    def _handle_winch(self, *args):
        #self.erase()  # Doesn't seem to help.
        self._measure_terminal()
        # TODO: Reprint the bar but at the new width.

    def update(self, test, number):
        """Draw an updated progress bar.

        At the moment, the graph takes a fixed width, and the test identifier
        takes the rest of the row, truncated from the left to fit.

        test -- the test being run
        number -- how many tests have been run so far, including this one

        """
        # TODO: Play nicely with absurdly narrow terminals. (OS X's won't even
        # go small enough to hurt us.)

        # Figure out graph:
        GRAPH_WIDTH = 14
        # min() is in case we somehow get the total test count wrong. It's tricky.
        num_markers = int(round(min(1.0, float(number) / self.max) * GRAPH_WIDTH))
        # If there are any markers, replace the last one with the spinner.
        # Otherwise, have just a spinner:
        markers = '=' * (num_markers - 1) + self._spinner.next()
        graph = '[%s%s]' % (markers, ' ' * (GRAPH_WIDTH - len(markers)))

        # Figure out the test identifier portion:
        test_path = nose_selector(test)
        cols_for_path = self.cols - len(graph) - 2  # 2 spaces between path & graph
        if len(test_path) > cols_for_path:
            test_path = test_path[len(test_path) - cols_for_path:]
        else:
            test_path += ' ' * (cols_for_path - len(test_path))

        # Put them together, and let simmer:
        self.last = tigetstr('bold') + test_path + '  ' + graph + tigetstr('sgr0')
        with AtLine(self.stream, self.lines):
            self.stream.write(self.last)

    def erase(self):
        """White out the progress bar."""
        with AtLine(self.stream, self.lines):
            self.stream.write(tigetstr('el'))
        self.stream.flush()

    def dodging(bar):
        """Return a context manager which erases the bar, lets you output things, and then redraws the bar."""
        class ShyProgressBar(object):
            """Context manager that implements a progress bar that gets out of the way"""

            def __enter__(self):
                """Erase the progress bar so bits of disembodied progress bar don't get scrolled up the terminal."""
                # My terminal has no status line, so we make one manually.
                bar.erase()

            def __exit__(self, type, value, tb):
                """Redraw the last saved state of the progress bar."""
                # This isn't really necessary unless we monkeypatch stderr; the
                # next test is about to start and will redraw the bar.
                with AtLine(bar.stream, bar.lines):
                    bar.stream.write(bar.last)
                bar.stream.flush()

        return ShyProgressBar()


class AtLine(object):
    """Context manager which moves the cursor to a certain line on entry and goes back to where it was on exit"""

    def __init__(self, stream, line):
        self.stream = stream
        self.line = line

    def __enter__(self):
        """Save position and move to progress bar, col 1."""
        self.stream.write(tigetstr('sc'))  # save position
        self.stream.write(tparm(tigetstr('cup'), self.line, 0))

    def __exit__(self, type, value, tb):
        self.stream.write(tigetstr('rc'))  # restore position


def nose_selector(test):
    """Return the string you can pass to nose to run `test`."""
    address = test_address(test)
    if not address:
        return 'Unknown test'
    file, module, rest = address

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
