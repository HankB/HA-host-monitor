#!/usr/bin/env python3

"""
Create (if needed) and update host records for the home automation host
monitor. In other words, manage the database that the monitor works from.

Usage:
    edit_hahmon.py -c                           # create database if doesn't exist
    edit_hahmon.py -a <hostname> [<topic>]      # add host to database
    edit_hahmon.py -d <hostname> [<topic>]      # remove host from database
    edit_hahmon.py -l [<hostname>]              # report status of listed host
                                                # or all hosts in database

    (see parse_args() for expanded argument names.)

To destroy the database simply delete the database file.

Database schema:
    host        Hostname of publisher.
    topic       MQTT topic if one is specified.
    timeout     Time at which the publisher is presumed to be unresponsive.
    timestamp   Time host last published (or when added to database.)
    status      Status of this host (and perhaps topic) [unknown|alive|late]

    (All fields text except for timeout and since which are integers.)

"""
import sqlite3
import atexit
import os
import time
from argparse import ArgumentParser


def close_connection(some_con):
    some_con.commit()
    some_con.close()


def open_database(db_name):
    try:
        conn = sqlite3.connect(db_name)
        atexit.register(close_connection, conn)
        return conn
    except:
        return None


# Create table
def create_database(db_name):
    if os.path.isfile(db_name):
        return 1
    try:
        conn = open_database(db_name)
        c = conn.cursor()

        st = c.execute('''CREATE TABLE host_activity
                (
                host        TEXT,
                topic       TEXT,
                timestamp   INTEGER,
                timeout     INTEGER,
                status      TEXT
                )''')
    except:
        return 2

    return 0


def host_match(cursor, name, topic=None):
    """ Check for matches with supplied values
    0 - no matches
    -1 - error
    n - number of matching rows (should be only 1)"""
    try:
        if topic is None:
            records = cursor.execute('''select count(*) from host_activity
                where host=? and topic is NULL''', (name,))
        else:
            records = cursor.execute('''select count(*) from host_activity
                where host=? and topic=?''', (name, topic,))
        return records.fetchone()[0]
    except:
        return -1


def insert_host(db_name, name, timeout, topic=None):
    """ Add a host to the database. Return an appropriate status:
    0 - Added
    1 - duplicate - host/topic already exists.
    2 - some other error
    """
    conn = open_database(db_name)
    if conn == None:
        return 2

    try:
        c = conn.cursor()
        match_result = host_match(c, name, topic)
        if match_result == 0:
            c.execute('''insert into host_activity values(?,?,?,?,?)''', (
                name, topic, int(time.time()), timeout, "unknown", ))
            conn.commit()
            rc = 0
        elif match_result == -1:
            rc = 2
        else:
            rc = 1
    except:
        rc = 2

    c.close()
    return rc


def update_host_timeout(db_name, name, timeout, topic=None):
    """ Update timeout setting for a host/topic in the database.
    Return an appropriate status:
    0 - Updated
    1 - Host does not exist in DB.
    2 - some other error
    NB: Only the timeout can be changed since the host and topic uniquely
    identify the record.
    """
    conn = open_database(db_name)
    if conn == None:
        return 2

    try:
        c = conn.cursor()
        match_result = host_match(c, name, topic)
        if match_result == 1:
            if topic == None:
                c.execute('''update host_activity set timeout=?
                        where host=? and topic is NULL''', (timeout, name, ))
            else:
                c.execute('''update host_activity set timeout=?
                        where host=? and topic=?''', (timeout, name, topic,))
            conn.commit()
            rc = 0
        elif match_result == -1:
            rc = 2
        else:
            rc = 1
    except:
        rc = 2
    finally:
        c.close()

    return rc


def list_unimplemented(db_name, name="%", topic=None):
    """ Create a text list of '\n' seperated records representing
    hosts and their respective records.
    TODO: For now return all rows. For my application that will meet needs.
    For that matter, an sqlite3 command would do.
        sqlite3 db_name 'select * from host_activity;'
    """
    conn = open_database(db_name)
    if conn == None:
        return (2, "")

    try:
        c = conn.cursor()
        if topic is None:
            records = cursor.execute('''select * from host_activity
                where host like ? ''', (name,))
        else:
            records = cursor.execute('''select count(*) from host_activity
                where host like ? and topic like ?''', (name, topic,))
    except:
        return -1
    finally:
        c.close()

    return rc

test_DB_name = "hahmon.db"


def parse_args(args):
    ''' Parse command line arguments in a testable fashion
    '''

    parser = ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-c", "--create",
                       action="store_true", dest="create", default=False,
                       help="create empty database")
    group.add_argument("-a", "--add",
                       dest="addhost", nargs='+',
                       help="add <hostname> [<topic>]")
    group.add_argument("-d", "--delete",
                       dest="delhost", nargs='+',
                       help="delete <hostname> [<topic>]")
    group.add_argument("-l", "--list",
                       dest="listhost", nargs='?', default="",
                       help="list [<hostname>]")
    return parser.parse_args(args)


def edit_hahmon_main():
    from sys import argv
    args = parse_args(argv[1:])

    print("args", args)

    print("main called\n")

if __name__ == "__main__":
    edit_hahmon_main()
