from curses import tigetstr, setupterm, tparm
from fcntl import ioctl
from functools import partial
from itertools import cycle
from os import getcwd
from os.path import abspath, realpath
from signal import signal, SIGWINCH
import struct
from termios import TIOCGWINSZ
from time import time
from traceback import format_list, extract_tb, format_exception_only

from nose.plugins import Plugin
from nose.exc import SkipTest
from nose.util import test_address, src


class ProgressivePlugin(Plugin):
    """Nose plugin which prioritizes the important information"""
    name = 'progressive'
    _testsRun = 0
    _totalTests = 0

    # TODO: Decrease score so we run early, and monkeypatch stderr in __init__.
    # See if that works.

    def begin(self):
        # nosetests changes directories to the tests dir when run from a
        # distribution dir, so save the original cwd.
        self._cwd = getcwd()

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

    def prepareTestLoader(self, loader):
        """Insert ourselves into loader calls to count tests.

        The top-level loader call often returns lazy results, like a LazySuite.
        This is a problem, as we would destroy the suite by iterating over it
        to count the tests. Consequently, we monkeypatch the top-level loader
        call to do the load twice: once for the actual test running and again
        to yield something we can iterate over to do the count.

        """
        def capture_suite(orig_method, *args, **kwargs):
            """Intercept calls to the loader before they get lazy.

            Re-execute them to grab a copy of the possibly lazy suite, and
            count the tests therein.

            """
            self._totalTests += orig_method(*args, **kwargs).countTestCases()
            return orig_method(*args, **kwargs)

        # TODO: If there's ever a practical need, also patch loader.suiteClass
        # or even TestProgram.createTests. createTests seems to be main top-
        # level caller of loader methods, and nose.core.collector() (which
        # isn't even called in nose) is an alternate one.
        if hasattr(loader, 'loadTestsFromNames'):
            loader.loadTestsFromNames = partial(capture_suite,
                                                loader.loadTestsFromNames)
        return loader

    def prepareTestRunner(self, runner):
        """Store start time so finalize() can use it.

        This is as close to the start of the run as we can get without being
        our own testrunner.

        """
        self._startTime = time()

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
        formatted_traceback = ''.join(format_list(extracted_tb))
        # TODO: Canonicalize the path to remove /kitsune/../kitsune nonsense.
        # Don't relativize, though, as that hurts the ability to paste into
        # running editors.
        writeln = self.stream.writeln
        write = self.stream.write
        with self.bar.dodging():
            writeln('\n' + tigetstr('bold') +
                    '%s: %s' % (kind, nose_selector(test)))

            # File name and line num in a format vi can take:
            address = test.address()
            if address:  # None if no such callable found. No sense trying to find the test frame if there's no such thing.
                file, line = frame_of_test(address, extracted_tb)[:2]
                writeln(' ' * len(kind) + '  +%s %s' %
                        (line, human_path(src(file), self._cwd)))

            write(tigetstr('sgr0'))  # end bold

            # Traceback:
            write(formatted_traceback)

            # Exception:
            write(''.join(format_exception_only(exception_type, exception_value)))

    def finalize(self, result):
        """Print counts of tests run."""
        def renderResultType(type, number):
            """Return a rendering like '2 failures', given a type like 'failure' and a number of them."""
            ret = '%s %s%s' % (number, type, 's' if number != 1 else '')
            if type in ['failure', 'error'] and number:
                ret = tigetstr('bold') + ret + tigetstr('sgr0')
            return ret

        types = ['test', 'failure', 'error']
        values = [self._testsRun, len(result.failures), len(result.errors)]
        if hasattr(result, 'skipped'):  # Absent if --no-skip is passed
            types.append('skip')
            values.append(len(result.skipped))
        msg = ', '.join(renderResultType(t, v) for t, v in zip(types, values)) + \
              ' in %.1fs' % (time() - self._startTime)

        # Erase progress bar. Bash doesn't clear the whole line when printing
        # the prompt, leaving a piece of the bar.
        self.bar.erase()
        self.stream.writeln()
        if not result.failures and not result.errors:
            self.stream.write('OK!  ')
        self.stream.writeln(msg)

    def startTest(self, test):
        # Overriding this seems to prevent TextTestRunner from running its, so
        # we have to keep track of the test count ourselves.
        self._testsRun += 1
        self.bar.update(test, self._testsRun)

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


def human_path(path, cwd):
    """Return the most human-readable representation of the given path.

    If an absolute path is given that's within the current directory, convert
    it to a relative path to shorten it. Otherwise, return the absolute path.

    """
    path = abspath(path)
    if path.startswith(cwd):
        path = path[len(cwd) + 1:]  # Make path relative. Remove leading slash.
    return path


class OneTrackMind(object):
    """An accurate simulation of my brain

    I can know one thing at a time, at some level of confidence. You can tell
    me other things, but if I'm not as confident of them, I'll forget them. If
    I'm more confident of them, they'll replace what I knew before.

    """
    def __init__(self):
        self.confidence = 0
        self.best = None

    def know(self, what, confidence):
        """Know something with the given confidence, and return self for chaining.

        If confidence is higher than that of what we already know, replace
        what we already know with what you're telling us.

        """
        if confidence > self.confidence:
            self.best = what
            self.confidence = confidence
        return self


def frame_of_test((test_file, test_module, test_call), extracted_tb):
    """Return the frame of a traceback that represents the given result of test_address().

    Sometimes this is hard. It takes its best guess.

    """
    test_file_path = realpath(test_file)
    # OneTrackMind helps us favor the latest frame, even if there's more than
    # one match of equal confidence.
    knower = OneTrackMind().know(extracted_tb[-1], 1)

    # TODO: Perfect. Right now, I'm just comparing by function name within a
    # module. This should break only if you have two identically-named
    # functions from a single module in the call stack when your test fails.
    # However, it bothers me. I'd rather be finding the actual callables and
    # comparing them directly.
    for frame in reversed(extracted_tb):
        file, line, function, text = frame
        if test_file_path == realpath(file):  # A test address always has a file, at least.
            knower.know(frame, 2)
            if function == test_call.rsplit('.')[-1]:
                knower.know(frame, 3)
                break
    return knower.best
