from functools import partial
from os import getcwd
import pdb
import sys

from nose.plugins import Plugin

from noseprogressive.runner import ProgressiveRunner
from noseprogressive.wrapping import cmdloop, set_trace, StreamWrapper


class ProgressivePlugin(Plugin):
    """Nose plugin which prioritizes the important information"""
    name = 'progressive'
    _totalTests = 0
    score = 10000  # Grab stdout and stderr before the capture plugin.

    def begin(self):
        """Wrap stderr and stdout to keep other users of them from smearing our progress bar."""
        # TODO: Do only if isatty.
        if not isinstance(sys.stdout, StreamWrapper):
            # Without the above check, these get double-wrapped due to our
            # reinvocation of the whole test stack to count the tests.
            sys.stderr = StreamWrapper(sys.stderr, self)  # TODO: Any point?
            sys.stdout = StreamWrapper(sys.stdout, self)

        self._set_trace = pdb.set_trace
        pdb.set_trace = set_trace

        self._cmdloop, pdb.Pdb.cmdloop = pdb.Pdb.cmdloop, cmdloop

        # nosetests changes directories to the tests dir when run from a
        # distribution dir, so save the original cwd.
        self._cwd = getcwd()

    def end(self):
        # TODO: This doesn't seem to get called!
        sys.stderr = sys.stderr.stream
        sys.stdout = sys.stdout.stream
        pdb.set_trace = self._set_trace
        pdb.Pdb.cmdloop = self._cmdloop

    def options(self, parser, env):
        super(ProgressivePlugin, self).options(parser, env)
        parser.add_option('--progressive-advisories',
                          action='store_true',
                          dest='showAdvisories',
                          default=env.get('NOSE_PROGRESSIVE_ADVISORIES', False),
                          help='Show skips and deprecation exceptions in '
                               'addition to failures and errors.')

    def configure(self, options, config):
        super(ProgressivePlugin, self).configure(options, config)
        if self.can_configure:
            self._showAdvisories = options.showAdvisories

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
                                 self._showAdvisories,
                                 verbosity=self.conf.verbosity,
                                 config=self.conf)  # So we don't get a default
                                                    # NoPlugins manager

    def prepareTestResult(self, result):
        self.bar = result.bar
