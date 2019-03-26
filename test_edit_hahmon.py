#!/usr/bin/env python3

"""
Test program for hahmon (Home Automation Host Monitor)
"""

import edit_hahmon
import unittest
import inspect
import pathlib
import os
import time
import subprocess
import sqlite3


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
db_path = pathlib.Path(test_DB_name)


class UpdateHAmonTest(unittest.TestCase):

    @classmethod
    def setUpClass(UpdateHAmonTest):
        if pathlib.Path.is_dir(db_path):
            pathlib.Path.rmdir(db_path)
        elif pathlib.Path.is_file(db_path):
            pathlib.Path.unlink(db_path)

    def validate_record(self, name, timestamp, timeout, topic=None):
        """ Read record from DB matching key and topic and validate contents' """
        if topic == None:
            select = '"select * from host_activity ' + \
                'where host=\'' + name + '\' and topic is NULL"'
        else:
            select = '"select * from host_activity ' + \
                'where host=\'' + name + '\' and topic=\'' + topic + '\'"'
        with os.popen('sqlite3 ha_test.db ' + select) as db_read:
            db_content = db_read.read()

        if topic == None:
            topic = ""

        self.assertTrue((db_content == name + '|' + topic + '|' + str(timestamp) + '|'
                         + str(timeout) + '|unknown\n') or
                        (db_content == name + '|' + topic + '|' + str(timestamp + 1) + '|'
                         + str(timeout) + '|unknown\n'))

    def populate_test_DB(self, dbname, contents):
        self.assertEqual(edit_hahmon.create_database(test_DB_name), 0,
                         "call create_database()")

        try:
            conn = sqlite3.connect(test_DB_name)
        except:
            self.assertTrue(False, "Cannot connect to DB")

        conn.executemany(
            "insert into host_activity(host, topic, timestamp, timeout, status) \
                values (?,?,?,?,?)", contents)
        conn.commit()
        edit_hahmon.close_connection(conn)

    def test_create_database(self):

        self.assertEqual(edit_hahmon.create_database(test_DB_name), 0,
                         "call create_database()")

        self.assertEqual(edit_hahmon.create_database(test_DB_name), 1,
                         "call create_database(), exists")

        pathlib.Path.unlink(db_path)
        pathlib.Path.mkdir(db_path)

        self.assertEqual(edit_hahmon.create_database(test_DB_name), 2,
                         "call create_database(), exists")

        pathlib.Path.rmdir(db_path)

    def test_host_match(self):
        self.assertEqual(edit_hahmon.create_database(test_DB_name), 0,
                         "call create_database()")

        hosts = [
            ("oak", None),
            ("oak", "/some/topic"),
            ("oak", "/another/topic"),
            ("oak", "/duplicate/topic"),
            ("oak", "/duplicate/topic"),
            ("maple", None),
            ("maple", "/some/topic"),
            ("maple", "/another/topic"),
        ]

        try:
            conn = sqlite3.connect(test_DB_name)
        except:
            self.assertTrue(False, "Cannot connect to DB")

        conn.executemany(
            "insert into host_activity(host, topic) values (?,?)", hosts)
        conn.commit()
        c = conn.cursor()

        self.assertEqual(edit_hahmon.host_match(
            c, "oak"), 1, "match host w/out topic")
        self.assertEqual(edit_hahmon.host_match(c, "oak", "no/topic"), 0,
                         "match host w/unmatched topic")
        self.assertEqual(edit_hahmon.host_match(c, "oak", "/some/topic"),
                         1, "match host w/ topic")
        self.assertEqual(edit_hahmon.host_match(c, "oak", "/duplicate/topic"),
                         2, "match host w/duplicate topic")  # pathological

        # comment next line to allow manual examination of database
        edit_hahmon.close_connection(conn)
        pathlib.Path.unlink(pathlib.Path(test_DB_name))

    def test_insert_host(self):
        self.assertEqual(edit_hahmon.create_database(test_DB_name), 0,
                         "call create_database()")

        # test insert, before and after times prevent race condition in subsequent test
        # Assumes it will not take more than one second to insert a line.
        timestamp_before = str(int(time.time()))
        self.assertEqual(
            edit_hahmon.insert_host(test_DB_name, "oak", 60 * 60), 0,
                         "call insert_host()")
        timestamp_after = str(int(time.time()))
        with os.popen('sqlite3 ha_test.db "select * from host_activity"') as db_read:
            db_content = db_read.read()

        self.assertTrue((db_content == "oak||" + timestamp_before + "|3600|unknown\n") or
                        (db_content == "oak||" +
                         timestamp_after + "|3600|unknown\n"),
                        "DB content match")

        # repeat insert should be rejected. DB contents should remain the same
        self.assertEqual(
            edit_hahmon.insert_host(test_DB_name, "oak", 60 * 60), 1,
                         "call insert_host()")

        with os.popen('sqlite3 ha_test.db "select * from host_activity"') as db_read:
            db_content = db_read.read()

        self.assertTrue((db_content == "oak||" + timestamp_before + "|3600|unknown\n") or
                        (db_content == "oak||" +
                         timestamp_after + "|3600|unknown\n"),
                        "DB content match")

        # test insert with a different host
        timestamp_before = str(int(time.time()))
        self.assertEqual(
            edit_hahmon.insert_host(test_DB_name, "olive", 60 * 60), 0,
                         "call insert_host()")
        timestamp_after = str(int(time.time()))

        with os.popen('''sqlite3 ha_test.db "select * from host_activity
                        where host=\'olive\'"''') as db_read:
            db_content = db_read.read()

        self.assertTrue((db_content == "olive||" + timestamp_before + "|3600|unknown\n") or
                        (db_content == "olive||" +
                         timestamp_after + "|3600|unknown\n"),
                        "DB content match")

        # Test insert with topic
        timestamp_before = str(int(time.time()))
        self.assertEqual(
            edit_hahmon.insert_host(test_DB_name, "oak", 60 * 60, "x"), 0,
                         "call insert_host()")
        timestamp_after = str(int(time.time()))
        with os.popen('''sqlite3 ha_test.db "select * from host_activity
                        where host=\'oak\' and topic=\'x\'"''') as db_read:
            db_content = db_read.read()

        self.assertTrue((db_content == "oak|x|" + timestamp_before + "|3600|unknown\n") or
                        (db_content == "oak|x|" +
                         timestamp_after + "|3600|unknown\n"),
                        "DB content match")

        # test duplicate rejection with topic
        self.assertEqual(
            edit_hahmon.insert_host(test_DB_name, "oak", 60 * 60, "x"), 1,
                         "call insert_host()")
        with os.popen('''sqlite3 ha_test.db "select * from host_activity
                        where host=\'oak\' and topic=\'x\'"''') as db_read:
            db_content = db_read.read()

        self.assertTrue((db_content == "oak|x|" + timestamp_before + "|3600|unknown\n") or
                        (db_content == "oak|x|" +
                         timestamp_after + "|3600|unknown\n"),
                        "DB content match")
        # Test insert with different topic
        timestamp_before = str(int(time.time()))
        self.assertEqual(
            edit_hahmon.insert_host(test_DB_name, "oak", 60 * 60, "y"), 0,
                         "call insert_host()")
        timestamp_after = str(int(time.time()))
        with os.popen('''sqlite3 ha_test.db "select * from host_activity
                        where host=\'oak\' and topic=\'y\'"''') as db_read:
            db_content = db_read.read()

        self.assertTrue((db_content == "oak|y|" + timestamp_before + "|3600|unknown\n") or
                        (db_content == "oak|y|" +
                         timestamp_after + "|3600|unknown\n"),
                        "DB content match")

        # comment next line to allow manual examination of database
        pathlib.Path.unlink(pathlib.Path(test_DB_name))

    def test_update_host_timeout(self):
        if os.path.isfile(test_DB_name):
            pathlib.Path.unlink(pathlib.Path(test_DB_name))
        self.assertEqual(edit_hahmon.create_database(test_DB_name), 0,
                         "call create_database()")
        timestamp_before = int(time.time())
        self.assertEqual(edit_hahmon.insert_host(test_DB_name, "oak", 300), 0,
                         "call insert_host()")
        self.assertEqual(edit_hahmon.insert_host(test_DB_name,
                                                 "oak", 500, "/some/topic"), 0,
                         "call insert_host()")
        timestamp_after = int(time.time())
        self.assertTrue(timestamp_after - timestamp_before <= 1,
                        "test error: process took too long")

        # Validate first and second record inserted
        self.validate_record("oak", timestamp_before, 300)
        self.validate_record("oak", timestamp_before, 500, "/some/topic")

        # Update first record
        self.assertEqual(
            edit_hahmon.update_host_timeout(test_DB_name, "oak", 350), 0,
                         "call update_host()")

        # Validate first and second record inserted
        self.validate_record("oak", timestamp_before, 350)
        self.validate_record("oak", timestamp_before, 500, "/some/topic")

        self.assertEqual(edit_hahmon.update_host_timeout(test_DB_name,
                                                         "oak", 3000, "/some/topic"), 0,
                         "call update_host()")

        # Validate first and second record inserted
        self.validate_record("oak", timestamp_before, 350)
        self.validate_record("oak", timestamp_before, 3000, "/some/topic")

        # comment next line to allow manual examination of database
        pathlib.Path.unlink(pathlib.Path(test_DB_name))

    def test_list(self):
        # create/populate database

        hosts = []  # empty DB
        self.populate_test_DB(test_DB_name, hosts)
        (status, results) = edit_hahmon.list_db(test_DB_name)
        self.assertEqual(status, 0, "non-zero status list_db()")
        self.assertEqual(results, [],
                         "empty DB did not return empty results list_db()")
        pathlib.Path.unlink(pathlib.Path(test_DB_name))

        hosts = [   # single entry in DB
            ("oak", None,               1553542680, 300, 'unknown'),
        ]
        self.populate_test_DB(test_DB_name, hosts)
        (status, results) = edit_hahmon.list_db(test_DB_name)
        self.assertEqual(status, 0, "non-zero status list_db()")
        self.assertEqual(
            results, ['oak None 1553542680 300 unknown'],
            "single entry DB did not return correct results ist_db()")
        pathlib.Path.unlink(pathlib.Path(test_DB_name))

        hosts = [
            ("oak", None,               1553542680, 300, 'unknown'),
            ("oak", "/some/topic",      1553542680, 300, 'unknown'),
            ("oak", "/someother/topic", 1553542680, 300, 'unknown'),
            ("maple", None,             1553542680, 300, 'unknown'),
            ("maple", "/some/topic",    1553542680, 300, 'unknown'),
        ]
        self.populate_test_DB(test_DB_name, hosts)
        (status, results) = edit_hahmon.list_db(test_DB_name)
        self.assertEqual(status, 0, "non-zero status list_db()")
        self.assertEqual(len(results), 5, "correct result count list_db()")
        self.assertEqual(
            results, ['oak None 1553542680 300 unknown',
                      'oak /some/topic 1553542680 300 unknown',
                      'oak /someother/topic 1553542680 300 unknown',
                      'maple None 1553542680 300 unknown',
                      'maple /some/topic 1553542680 300 unknown',
                      ],
            "multiple entry DB did not return correct results ist_db()")

        ''' uncomment to view list results
        for row in results:
            print(row)
        '''

        # comment next line to allow manual examination of database
        pathlib.Path.unlink(pathlib.Path(test_DB_name))

    def test_parse_args(self):
        import sys

        class NullDevice:

            def write(self, s):
                pass
        sys.stderr = NullDevice()
                                # suppress output to STDERR generated by
                                # successful test

        # test invalid argument
        with self.assertRaises(SystemExit, msg="exit on [-x]"):
            edit_hahmon.parse_args(['-x'])

        # test absence of arguments
        with self.assertRaises(SystemExit, msg="exit on zero args"):
            edit_hahmon.parse_args([])

        # test 'create' arguments
        args = edit_hahmon.parse_args(['-c'])
        self.assertTrue(args.db_name == None, "Returned db_name != None")
        self.assertTrue(args.addhost == None and args.delhost == None
                        and args.listhost == '', "Returned wrong defaults [-c]")

        # test 'create' arguments
        args = edit_hahmon.parse_args(['-c', 'path/to/db'])
        self.assertTrue(
            args.db_name == 'path/to/db', "Returned db_name != 'path/to/db'")
        self.assertTrue(args.addhost == None and args.delhost == None
                        and args.listhost == '', "Returned wrong defaults [-c]")

        with self.assertRaises(SystemExit, msg="exit on superfluous arg"):
            edit_hahmon.parse_args(['-c', 'path/to/db', 'superfluous'])

        args = edit_hahmon.parse_args(['--create', 'path/to/database'])
        self.assertTrue(args.db_name == 'path/to/database',
                        "Returned db_name != 'path/to/database'")
        self.assertTrue(args.addhost == None and args.delhost == None
                        and args.listhost == '', "Returned wrong defaults [--create]")

        args = edit_hahmon.parse_args(['--create'])
        self.assertTrue(args.db_name == None, "Returned db_name != None")
        self.assertTrue(args.addhost == None and args.delhost == None
                        and args.listhost == '', "Returned wrong defaults [--create]")

        # test 'add' arguments
        with self.assertRaises(SystemExit, msg="didn't exit on [-a]"):
            edit_hahmon.parse_args(['-a'])

        args = edit_hahmon.parse_args(['-a', 'somehost'])
        self.assertEqual(args.addhost[0], "somehost",
                         "didn't return 'somehost'")
        self.assertTrue(args.db_name == '' and args.delhost == None
                        and args.listhost == '', "Returned wrong defaults ['-a', 'somehost']")

        args = edit_hahmon.parse_args(['-a', 'somehost', 'sometopic'])
        self.assertEqual(args.addhost[0], "somehost",
                         "didn't return 'somehost'")
        self.assertEqual(args.addhost[1], "sometopic",
                         "didn't return 'sometopic'")
        self.assertTrue(args.db_name == '' and args.delhost == None
                        and args.listhost == '', "Returned wrong defaults ['-a', 'somehost', 'sometopic']")

        with self.assertRaises(SystemExit,
                               msg="exit on superfluous arg ['-a', 'somehost', 'sometopic', 'superfluous']"):
            edit_hahmon.parse_args(
                ['-a', 'somehost', 'sometopic', 'superfluous'])

        # test 'delete' arguments
        with self.assertRaises(SystemExit, msg="didn't exit on [-d]"):
            edit_hahmon.parse_args(['-d'])

        args = edit_hahmon.parse_args(['-d', 'somehost'])
        self.assertEqual(args.delhost[0], "somehost",
                         "didn't return 'somehost'")
        self.assertTrue(args.db_name == '' and args.addhost == None
                        and args.listhost == '', "Returned wrong defaults ['-d', 'somehost']")

        args = edit_hahmon.parse_args(['-d', 'somehost', 'sometopic'])
        self.assertEqual(args.delhost[0], "somehost",
                         "didn't return 'somehost'")
        self.assertEqual(args.delhost[1], "sometopic",
                         "didn't return 'sometopic'")
        self.assertTrue(args.db_name == '' and args.addhost == None
                        and args.listhost == '', "Returned wrong defaults ['-d', 'somehost', 'sometopic']")

        with self.assertRaises(SystemExit,
                               msg="exit on superfluous arg ['-d', 'somehost', 'sometopic', 'superfluous']"):
            edit_hahmon.parse_args(
                ['-d', 'somehost', 'sometopic', 'superfluous'])

        # test --list arg processing
        # non-intuitively "nargs='?'" returns None for '-l'
        args = edit_hahmon.parse_args(['-l'])
        self.assertEqual(args.listhost, None, "['-l'] didn't return None")
        args = edit_hahmon.parse_args(['-l', 'somehost'])
        self.assertEqual(args.listhost, "somehost",
                         "['-l', 'somehost'] didn't return 'somehost'")
        '''
        self.assertEqual(args.addhost[1], "sometopic", "didn't return 'sometopic'")
        self.assertEqual(args.addhost[2], "superfluous", "didn't return 'superfluous'")
        self.assertTrue( args.db_name == '' and args.delhost == None
            and args.listhost == '', "Returned wrong defaults ['-a', 'somehost', 'sometopic']")
        '''


if __name__ == "__main__":
    unittest.main()
