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
    host    Hostname of publisher.
    topic   MQTT topic if one is specified.
    timeout Time at which the publisher is presumed to be unresponsive.
    status  Status of this host (and perhaps topic) [unknown|alive|late]

    (All fields text except for timeout which is an integer.)

"""

def create_database(name):
    return 0

