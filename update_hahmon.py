#!/usr/bin/env python3

"""
Create (if needed) and update host records for the home automation host 
monitor.

Usage:
    update_hahmon.py -a <hostname> [<topic>]    # add host to database
    update_hahmon.py -d <hostname> [<topic>]    # remove host from database
    update_hahmon.py -l [<hostname>]            # report status of listed host
    or all hosts in database

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
                timeout     INTEGER,
                timestamp   INTEGER,
                status      TEXT
                )''')
    except:
        return 2

    return 0

def insert_host(db_name, name, timeout, topic=None):
    """ Add a host to the database. Return an appropriate status:
    0 - Added
    1 - duplicate - host/topic already exists.
    2 - overlap - host exists but requiested topic or existing topic is None
    3 - some other error
    """
    conn = open_database(db_name)
    c = conn.cursor()
    records = c.execute('select * from host_activity where host="'+name+'"')

    c.execute('''insert into host_activity values(?,?,?,?,?)''', (name, topic, int(time.time()), timeout, "unknown", ))
    conn.commit()
    records = c.execute('select * from host_activity where host="'+name+'"')
    print( "queried and found ", records.rowcount , " records\n")
    for row in records:
        print(row)
    if conn == None:
        return 3
    return 0

