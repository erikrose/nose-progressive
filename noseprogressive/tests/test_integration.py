from unittest import TestCase, TestSuite

from nose import SkipTest
from nose.plugins import PluginTester
from nose.plugins.skip import Skip
from nose.tools import eq_

from noseprogressive import ProgressivePlugin


class IntegrationTestCase(PluginTester, TestCase):
    activate = '--with-progressive'
    plugins = [ProgressivePlugin(), Skip()]


class HookTests(IntegrationTestCase):
    """Tests that ensure our code is getting run when expected"""

    def makeSuite(self):
        class Failure(TestCase):
            def runTest(self):
                assert False

        class Skip(TestCase):
            def runTest(self):
                raise SkipTest

        class Success(TestCase):
            def runTest(self):
                pass

        class Error(TestCase):
            def runTest(self):
                raise NotImplementedError

        return TestSuite([Failure(), Skip(), Success(), Error()])

    @property
    def _output_str(self):
        """Return the capture output as a string."""
        return self.output._buf

    def test_fail(self):
        """Make sure failed tests print a line."""
        # Grrr, we seem to get stdout here, not stderr.
        eq_(self._output_str.count('FAIL: '), 1)

    def test_skip(self):
        """Make sure skipped tests print a line."""
        eq_(self._output_str.count('SKIP: '), 1)

    def test_error(self):
        eq_(self._output_str.count('ERROR: '), 1)


# def test_slowly():
#     def failer(y):
#         print "booga"
#         if y == 1:
#             assert False
#     for x in range(10):
#         from time import sleep
#         sleep(0.1)
#         yield failer, x


# def test_syntax_error():
#     x = 1
#     :bad
