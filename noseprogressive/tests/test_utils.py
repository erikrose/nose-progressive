from os import chdir, getcwd
from os.path import dirname, basename
from unittest import TestCase

from nose.tools import eq_

from noseprogressive.utils import human_path, frame_of_test


class UtilsTests(TestCase):
    """Tests for independent little bits and pieces"""

    def test_human_path(self):
        chdir(dirname(__file__))
        eq_(human_path(__file__, getcwd()), basename(__file__))

    def test_frame_of_test_null_file(self):
        """Make sure frame_of_test() doesn't crash when test_file is None."""
        try:
            frame_of_test((None, None, None), NotImplementedError,
                          NotImplementedError(), [('file', 333)])
        except AttributeError:
            self.fail('frame_of_test() raised AttributeError.')
