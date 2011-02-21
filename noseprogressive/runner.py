from time import time

import nose.core

from noseprogressive.result import ProgressiveResult


class ProgressiveRunner(nose.core.TextTestRunner):
    """Test runner that makes a lot less noise than TextTestRunner"""

    def __init__(self, cwd, totalTests, stream, **kwargs):
        super(ProgressiveRunner, self).__init__(stream, **kwargs)
        self._cwd = cwd
        self._totalTests = totalTests

    def _makeResult(self):
        """Return a Result that doesn't print dots.

        Nose's ResultProxy will wrap it, and other plugins can still print
        stuff---but without smashing into our progress bar, care of
        ProgressivePlugin's stderr/out wrapping.

        """
        return ProgressiveResult(self._cwd,
                                 self._totalTests,
                                 self.stream,
                                 config=self.config)

    def run(self, test):
        "Run the given test case or test suite...quietly."
        # These parts of Nose's pluggability are baked into
        # nose.core.TextTestRunner. Reproduce them:
        wrapper = self.config.plugins.prepareTest(test)
        if wrapper is not None:
            test = wrapper
        wrapped = self.config.plugins.setOutputStream(self.stream)
        if wrapped is not None:
            self.stream = wrapped

        result = self._makeResult()
        startTime = time()
        test(result)
        stopTime = time()

        # We don't care to hear about errors again at the end; we take care of
        # that in result.addError(), while the tests run.
        # result.printErrors()
        #
        # However, we do need to call this one useful line from
        # nose.result.TextTestResult's implementation of printErrors() to make
        # sure other plugins get a chance to report:
        self.config.plugins.report(self.stream)

        result.printSummary(startTime, stopTime)
        self.config.plugins.finalize(result)
        return result
