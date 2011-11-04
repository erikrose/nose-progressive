from os import chdir, getcwd
from os.path import dirname, basename
from unittest import TestCase

from nose.tools import eq_

from noseprogressive.utils import human_path, index_of_test_frame


def test_human_path():
    chdir(dirname(__file__))
    eq_(human_path(__file__, getcwd()), basename(__file__))


def test_index_of_test_frame():
    extracted_tb = \
        [('/nose/loader.py', 379, 'loadTestsFromName', 'addr.filename, addr.module)'),
         ('/nose/importer.py', 39, 'importFromPath', 'return self.importFromDir(dir_path, fqname)'),
         ('/nose/importer.py', 86, 'importFromDir', 'mod = load_module(part_fqname, fh, filename, desc)')]
    eq_(index_of_test_frame(extracted_tb,
                            SyntaxError,
                            SyntaxError('invalid syntax',
                                        ('/elasticutils/tests/tests.py', 120, 9, "        {'fields': ['id'],\n")),
                            'sometest'),  # This is an invalid thing to pass for
                                          # this arg, but it never uses it if
                                          # it receives a SyntaxError.
        None)
