from os import chdir, getcwd
from os.path import dirname, basename, realpath
from unittest import TestCase

from nose.tools import eq_
from nose.util import src

from noseprogressive.utils import human_path, index_of_test_frame


class DummyCase(TestCase):
    """A mock test to be thrown at ``index_of_test_frame()``

    Significantly, it's in the same file as the tests which use it, so the
    frame-finding heuristics can find a match.

    """
    def runTest(self):
        pass
dummy_test = DummyCase()


def test_human_path():
    chdir(dirname(__file__))
    eq_(human_path(__file__, getcwd()), basename(__file__))


def test_index_when_syntax_error_in_test_frame():
    """Make sure ``index_of_test_frame()`` returns None for SyntaxErrors in the test frame.

    When the SyntaxError is in the test frame, the test frame doesn't show up
    in the traceback. We reproduce this below by not referencing.

    """
    extracted_tb = \
        [('/nose/loader.py', 379, 'loadTestsFromName', 'addr.filename, addr.module)'),
         ('/nose/importer.py', 39, 'importFromPath', 'return self.importFromDir(dir_path, fqname)'),
         ('/nose/importer.py', 86, 'importFromDir', 'mod = load_module(part_fqname, fh, filename, desc)')]
    eq_(index_of_test_frame(extracted_tb,
                            SyntaxError,
                            SyntaxError('invalid syntax',
                                        ('tests.py', 120, 1, "{'fields': ['id'],\n")),
                            dummy_test),
        None)


def test_index_when_syntax_error_below_test_frame():
    """Make sure we manage to find the test frame if there's a SyntaxError below it.

    Here we present to ``index_of_test_frame()`` a traceback that represents
    this test raising a SyntaxError indirectly, in a function called by same
    test.

    """
    extracted_tb = [('/nose/case.py', 183, 'runTest', 'self.test(*self.arg)'),
                    # Legit path so the frame finder can compare to the address of DummyCase:
                    (src(realpath(__file__)), 34, 'test_index_when_syntax_error_below_test_frame', 'deeper()'),
                    ('/noseprogressive/tests/test_utils.py', 33, 'deeper', 'import noseprogressive.tests.syntaxerror')]
    eq_(index_of_test_frame(extracted_tb,
                            SyntaxError,
                            SyntaxError('invalid syntax',
                                        ('/tests/syntaxerror.py', 1, 1, ':bad\n')),
                            dummy_test),
        1)
