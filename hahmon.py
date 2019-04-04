#!/usr/bin/env python3
'''
Monitor hosts
Read output of mosquitto_sub
e.g. `mosquitto_sub -v -h oak -t \#`
Process all messages and update the database according to
the incoming messages.

This fiunction is broken into two files. This one will implement the code
needed for either of two variants. One variant will implement using the
module paho-mqtt and the other will use an external program `mosquitto_sub`
to receive messages from the broker.
'''

import re
import sqlite3
import atexit
from argparse import ArgumentParser


def close_db_connection(some_con):
    some_con.commit()
    some_con.close()

''' open database and return a connection and cursor
'''


def open_db_connection(db_name):
    conn = sqlite3.connect(db_name)
    atexit.register(close_db_connection, conn)
    c = conn.cursor()
    return (conn, c)


def parse_MQTT_msg(line):
    # typical is
    # 'home_automation/sodus/master_bedroom/temp_humidity 1553831160, 72.50, 30.98'
    # We ignore up to and including the first slash ('home_automation/sodus/')
    # (which may some day be shortened to '/ha')
    # We grab up to the next slash to ID the host ('sodus')
    # We gab the rest of the topic ('/master_bedroom/temp_humidity')
    # We grab the timestamp and convert to an integer. ('1553831160')
    # Return a tuple consisting of (host, topic, timestamp,)
    # Return None if the line cannot be parsed.
    # Note: Whereas ...
    fields = re.split('\W+', line)  # now split on space, comma
    if len(fields) < 6:     # 4 portions of topic, timestamp and rest of payload
        return None
    host = fields[1]
    topic = '/' + fields[2] + '/' + fields[3]
    if len(fields) < 4:
        return None
    timestamp = int(fields[4])
    return (host, topic, timestamp,)

''' parse_args()
Parse command line arguments in a testable fashion
'''


def parse_args(args):

    parser = ArgumentParser()
    parser.add_argument("-d", "--db_name",
                        dest="db_name", nargs=1,       # 1 argument
                        required=True,
                        help="/path/to/database")
    parser.add_argument("-b", "--broker",
                        dest="broker", nargs=1,       # 1 argument
                        required=True,
                        help="MQTT broker host name")

    parsed_args = parser.parse_args(args)

    return parsed_args
