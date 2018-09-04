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
                timestamp   INTEGER,
                timeout     INTEGER,
                status      TEXT
                )''')
    except:
        return 2

    return 0

def host_match(cursor, name, topic):
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
                where host=? and topic=?''', (name,topic,))
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
            c.execute('''insert into host_activity values(?,?,?,?,?)''', (name, topic, int(time.time()), timeout, "unknown", ))
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

def update_host_activity(db_name, str):
    ''' Update the host timestamp value for the given activity. Input string
    looks like
    "home_automation/brandywine/roamer/outside_temp_humidity 1536080280, 92.36, 58.06"
    where the host name is embedded in the 'topic' In this case the topic is
    taken to be "home_automation/brandywine/roamer/outside_temp_humidity" and
    the host is "brandywine". The timestamp is included in these messages by
    convention but is taken form the system monitoring the feed.
    Return an appropriate status:
    0 - Updated
    1 - Host/topic not found.
    2 - some other error
   '''
    topic = str.split()[0]
    host = topic.split('/')[1]

    conn = open_database(db_name)
    if conn == None:
        return 2

    try:
        c = conn.cursor()
        match_result = host_match(c, name, topic)
        if match_result == 1: # host/topic found
            c.execute('''update host_activity set timestamp=?
                    where host=? and topic=?''', (int(time.time()), name, topic,))
            conn.commit()
            rc = 0
        elif match_result == -1: # no match on host/topic
            match_result = host_match(c, name, None) # see if host with no topic exists
            if match_result == 1:   # host/None matchec
                c.execute('''update host_activity set timestamp=?
                        where host=? and topic=?''', (int(time.time()), name, topic,))
                conn.commit()
                rc = 0
            elif match_result == -1: # still not found
                rc = 1
            else:
                rc = 2
        else:
            rc = 2
    except:
        rc = 2
    finally:
        c.close()

    return rc
