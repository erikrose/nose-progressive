from os.path import dirname, join
from unittest import TestCase, TestSuite

from nose.plugins import PluginTester
from nose.plugins.skip import Skip

from noseprogressive import ProgressivePlugin


class IntegrationTestCase(PluginTester, TestCase):
    activate = '--with-progressive'
    plugins = [ProgressivePlugin(), Skip()]


class FailureTests(IntegrationTestCase):
    """Tests for behavior upon failure of a test"""

    def makeSuite(self):
        class SomeTests(TestCase):
            def runTest(self):
                """Fail."""
                assert False
        return TestSuite([SomeTests()])

    def test_fail(self):
        """Make sure skipped tests print a line."""
        import pdb;pdb.set_trace()
        # Grrr, we seem to get stdout here, not stderr.
        assert 'FAIL: ' in self.output
