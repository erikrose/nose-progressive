from functools import partial
from os import getcwd
import sys

from nose.plugins import Plugin

from noseprogressive.runner import ProgressiveRunner


class ProgressivePlugin(Plugin):
    """Nose plugin which prioritizes the important information"""
    name = 'progressive'
    _totalTests = 0
    score = 10000  # Grab stdout and stderr before the capture plugin.

    def begin(self):
        """Wrap stderr and stdout to keep other users of them from smearing our progress bar."""
        class StreamWrapper(object):
            def __init__(me, stream):
                me._stream = stream

            def __getattr__(me, name):
                return getattr(me._stream, name)

            def write(me, data):
                if hasattr(self, '_bar'):
                    with self._bar.dodging():
                        me._stream.write(data)
                else:
                    # Some things write to stderr before the bar is inited.
                    me._stream.write(data)

        # TODO: Do only if isatty.
        self._stderr = sys.stderr
        self._stdout = sys.stdout
        sys.stderr = StreamWrapper(sys.stderr)
        sys.stdout = StreamWrapper(sys.stdout)

        # nosetests changes directories to the tests dir when run from a
        # distribution dir, so save the original cwd.
        self._cwd = getcwd()

    def end(self):
        sys.stderr = self._stderr
        sys.stdout = self._stdout

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
        """Replace TextTestRunner with something that prints fewer dots."""
        return ProgressiveRunner(self._cwd,
                                 self._totalTests,
                                 runner.stream,
                                 verbosity=self.conf.verbosity,
                                 config=self.conf)  # So we don't get a default
                                                    # NoPlugins manager

    def prepareTestResult(self, result):
        self._bar = result.bar
