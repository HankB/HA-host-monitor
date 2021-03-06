#!/usr/bin/env python3

"""
Create (if needed) and update host records for the home automation host
monitor. In other words, manage the database that the monitor works from.

Usage:
    edit_hahmon.py -c [<path/to/db>]                    # create database if doesn't exist
    edit_hahmon.py -a <hostname> [<timeout>[<topic>]]   # add host to database
    edit_hahmon.py -d <hostname> [<topic>]              # remove host from database
    edit_hahmon.py -l [<hostname>]                      # report status of listed host
                                                        python3 # or all hosts in database

    (see parse_args() for expanded argument names.)
    For all options except -c must provide an environment variable DB_NAME_ENV to
    indicate where to find the database

To destroy the database simply delete the database file.

Database schema - one table:
    host        Hostname of publisher.
    topic       MQTT topic if one is specified.
    timeout     Time at which the publisher is presumed to be unresponsive.
    timestamp   Time host last published (or when added to database.)
    status      Status of this host (and perhaps topic) [unknown|alive|late]

    (All fields text except for timeout and since which are integers.)

"""
import sqlite3
import os
import sys
import time
from argparse import ArgumentParser


def close_connection(some_con):
    some_con.commit()
    some_con.close()


def open_database(db_name):
    try:
        conn = sqlite3.connect(db_name)
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
            # conn.commit()
            rc = 0
        elif match_result == -1:
            rc = 2
        else:
            rc = 1
    except:
        rc = 2

    close_connection(conn)
    return rc


def delete_host(db_name, name, topic=None):
    """ Delete a host from the database. Return an appropriate status:
    0 - Deleted
    1 - host/topic not found.
    2 - some other error
    """
    conn = open_database(db_name)
    if conn == None:
        return 2

    try:
        c = conn.cursor()
        match_result = host_match(c, name, topic)
        if match_result == 1:
            if topic is not None:
                rc = c.execute(
                    '''delete from host_activity where host=? and topic=?''',
                    (name, topic))
            else:
                rc = c.execute(
                    '''delete from host_activity where host=? and topic is NULL''',
                    (name,))

            conn.commit()
            rc = 0
        elif match_result == -1:
            rc = 2
        else:
            rc = 1
    except sqlite3.OperationalError as msg:
        print("delete_host:except", msg)
        rc = 2

    finally:
        close_connection(conn)

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


def list_db(db_name, name=None, topic=None):
    """ Create a text list of '\n' seperated records representing
    hosts and their respective records.
    TODO: For now return all rows. For my application that will meet needs.
    For that matter, an sqlite3 command would do.
        sqlite3 db_name 'select * from host_activity;'

    NB: Not possible to search for records with NULL topics
        as 'topic=None' interprets as 'any'
    """

    conn = open_database(db_name)

    if conn == None:
        return (2, "")

    if name is None:    # none implies all hosts
        name = '%'

    rc = (0, "")    # initialize return value
    try:
        c = conn.cursor()
        if topic is None:
            records = c.execute('''select * from host_activity
                where host like ? ''', (name,))
        elif topic is not None and name is None:
            records = c.execute('''select * from host_activity
                where  topic like ?''', (topic,))
        else:
            records = c.execute('''select * from host_activity
                where host like ? and topic like ?''', (name, topic,))
        result_array = []
        result_format = "{} {} {} {} {}"
        for rows in records:    # format and add rows to return value
            result_array.append(result_format.format(*rows))
        rc = (0, result_array)
    except:
        rc = (-1, "")
    finally:
        close_connection(conn)

    return rc


test_DB_name = "hahmon.db"


def usage_msg(name=None):
    return '''edit_hahmon.py
    [-c | --create [<path/to/database>] - create new database
    [-a | --add <hostname> [<timeout>] [<topic>]] - add host (must include timeout if
                                                    specifying topic)
    [-d | --delete <hostname> [<topic>] - delete matching host and topic
    [-l | --list [<hostname>] - list database for all hosts or selected host
    '''


def parse_args(args):
    ''' Parse command line arguments in a testable fashion
    '''

    parser = ArgumentParser(usage=usage_msg())
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-c", "--create",
                       dest="db_name", nargs='?',       # 0-1 arguments
                       default="",
                       help="create empty database")
    group.add_argument("-a", "--add",                   # 1-3 arguments
                       dest="addhost", nargs='+',
                       help="add <hostname> [<timeout sec> [<topic>]]")
    group.add_argument("-d", "--delete",                # 1-2 arguments
                       dest="delhost", nargs='+',
                       help="delete <hostname> [<topic>]")
    group.add_argument("-l", "--list",                  # 1-2 arguments
                       dest="listhost", nargs='?', default="",
                       help="list [<hostname>]")
    group.add_argument("-u", "--update_timeout",        # 3 arguments
                       dest="listhost", nargs=3, default="",
                       help="list [<hostname>]")

    parsed_args = parser.parse_args(args)

    # manual validation of arg count for --add
    if (parsed_args.addhost is not None) and (len(parsed_args.addhost) > 3):
        parser.error(
            '[-a|--addhost] accepts 1 to 3 arguments, not {}.'.format(len(parsed_args.addhost)))

    # manual validation of arg count for --delete
    if (parsed_args.delhost is not None) and (len(parsed_args.delhost) > 2):
        parser.error(
            '[-a|--delete] accepts 1 or 2 arguments, not {}.'.format(len(parsed_args.delhost)))

    return parsed_args


def edit_hahmon_main():
    from sys import argv
    args = parse_args(argv[1:])
    print("args", args)
    print(os.environ.get('HAMON_DB'))

    DB_NAME_ENV = 'DB_NAME_ENV'

    if args.db_name != "":      # create new DB?
        hamon_db = "hahmon.db"  # default database name
        if args.db_name != None:
            hamon_db = args.db_name
        rc = create_database(hamon_db)
        if rc != 0:
            print("could not create database: return code:", rc)
        else:
            print("created database", hamon_db)
            print("set ENV variale for using other options")
            print("e.g.'export DB_NAME_ENV=" + os.getcwd() + '/' + hamon_db)
        exit(rc)
    else:
        hamon_db = os.environ.get(DB_NAME_ENV)
        if hamon_db is None:
            print('Please specify the database location')
            print('e.g. \'export  DB_NAME_ENV=path/to/database\'')
            exit(1)

        print("DB is ", hamon_db)
        if args.addhost is not None:  # Add a host/timeout/topic
                                        # oops - no way to add timeout
            topic = None
            if len(args.addhost) == 3:
                topic = args.addhost[2]
                timeout = args.addhost[1]
            elif len(args.addhost) == 2:
                timeout = args.addhost[1]
            else:
                timeout = 300

            rc = insert_host(hamon_db, args.addhost[0], timeout, topic)
            if rc != 0:
                print(
                    "Insert '%s' '%s' not successful:%d" % (args.addhost[0], topic, rc))
                exit(rc)
        elif args.delhost is not None:  # delete a host
            topic = None
            if len(args.delhost) == 2:
                topic = args.delhost[1]
            else:
                topic = None
            rc = delete_host(hamon_db, args.delhost[0], topic)
            if rc == 0:
                print("Deleted host:", args.delhost[
                      0], "topic:", topic, "from", hamon_db)
            else:
                print("could not delete host:", args.delhost[
                      0], "topic:", topic, "from", hamon_db, "rc:", rc)
            exit(1)
        elif args.listhost != '':
            print("args.listhost", args.listhost)
            entries = list_db(hamon_db, args.listhost)
            print(entries)


if __name__ == "__main__":
    edit_hahmon_main()
