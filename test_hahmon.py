#!/usr/bin/env python3

"""
Test program for hahmon (Home Automation Host Monitor)
"""

import update_hahmon
import unittest
import inspect
import pathlib

def unittest_verbosity():
    """Return the verbosity setting of the currently running unittest
    program, or 0 if none is running.
    from https://stackoverflow.com/questions/13761697/
    """
    frame = inspect.currentframe()
    while frame:
        self = frame.f_locals.get('self')
        if isinstance(self, unittest.TestProgram):
            return self.verbosity
        frame = frame.f_back
    return 0

test_DB_name = "ha_test.db"
dp_path=pathlib.Path(test_DB_name)

class UpdateHAmonTest(unittest.TestCase):

    @classmethod
    def setUpClass(UpdateHAmonTest):
        if pathlib.Path.is_dir(dp_path):
            pathlib.Path.rmdir(dp_path)
        elif pathlib.Path.is_file(dp_path):
            pathlib.Path.unlink(dp_path)

    def test_create_database(self):

        self.assertEqual(update_hahmon.create_database(test_DB_name), 0,
                        "call create_database()")

        self.assertEqual(update_hahmon.create_database(test_DB_name), 1,
                        "call create_database(), exists")

        pathlib.Path.unlink(dp_path)
        pathlib.Path.mkdir(dp_path)

        self.assertEqual(update_hahmon.create_database(test_DB_name), 2,
                        "call create_database(), exists")
        
        pathlib.Path.rmdir(dp_path)

    def test_insert_host(self):
        self.assertEqual(update_hahmon.create_database(test_DB_name), 0,
                        "call create_database()")

        self.assertEqual(update_hahmon.insert_host(test_DB_name, "oak", 60*60), 0,
                        "call insert_host()")

       # pathlib.Path.unlink(pathlib.Path(test_DB_name))

if __name__ == "__main__": 
    unittest.main()