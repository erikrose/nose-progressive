from os import chdir, getcwd
from os.path import dirname, basename
from unittest import TestCase

from nose.tools import eq_

from noseprogressive import human_path


class UnitTests(TestCase):
    """Tests for independent little bits and pieces"""

    def test_human_path(self):
        chdir(dirname(__file__))
        eq_(human_path(__file__, getcwd()), basename(__file__))
