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
        stuff---but without smashing into my progress bar, care of my
        stderr/out wrapping.

        """
        return ProgressiveResult(self._cwd, self._totalTests, self.stream)

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
        timeTaken = stopTime - startTime
        result.printErrorsForReal(timeTaken)  # TODO: Why the hell does this dispatch to _TextTestResult if I call it printErrors?!
        self.config.plugins.finalize(result)
        return result
