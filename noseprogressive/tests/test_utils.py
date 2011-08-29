from os import chdir, getcwd
from os.path import dirname, basename
from unittest import TestCase

from nose.tools import eq_

from noseprogressive.utils import human_path, index_of_test_frame


class UtilsTests(TestCase):
    """Tests for independent little bits and pieces"""

    def test_human_path(self):
        chdir(dirname(__file__))
        eq_(human_path(__file__, getcwd()), basename(__file__))

    def test_index_of_test_frame_null_file(self):
        """Make sure index_of_test_frame() doesn't crash when test_file is None."""
        try:
            index_of_test_frame([('file', 333)], NotImplementedError,
                                NotImplementedError(), 'kersmoo')
        except AttributeError:
            self.fail('frame_of_test() raised AttributeError.')
