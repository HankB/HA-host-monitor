#!/usr/bin/env python3

"""
Test program for hahmon (Home Automation Host Monitor)
"""

import update_hahmon
import unittest
import inspect

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

class UpdateHAmonTest(unittest.TestCase):
     def test_create_database(self):
         print("update_hahmon.create_database(test_DB_name)",
                update_hahmon.create_database(test_DB_name), "\n")
         self.assertEqual(update_hahmon.create_database(test_DB_name), 0,
                "call create_database()")

if __name__ == "__main__": 
    unittest.main()