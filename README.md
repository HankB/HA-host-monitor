# HA-host-monitor

(Home Automation host monitor)

Monitor hosts that publish to an MQTT server to detect when one drops out.
(It will be useful to understand MQTT and related terminology.)

## Strategy

Use the Mosquitto client `mosquitto_sub` to subscribe to the MQTT server
and read/parse all of the updates. Host and update time will be will be
updated in an SQLite database. If the host does not exist in the database
an exception report will be sent. Periodically The database is scanned and
the time since last update compared to a constant stored in the database
and an exception reported for any overdue hosts.

## Components

1. Process to create and edit database entries.
1. Process to handle incoming MQTT messages and update the database.
1. Process to scan the database and look for overdue hosts.
1. Test script(s) to test portions of the various other components.

## Files

(It's a pain to come back after several months and not be able to figure out where I was.)

```test
edit_hahmon.py          create and update database.
hahmon.py               placeholder for the 'main'
test_edit_hahmon.py     unit tests for edit_hahmon.py
update_hahmon.py        ? holds presently unused code?
```

## Status

Working on the process to create and add/remove hosts in the database. (TDD - one test coded.)

## Testing

```bash
./test_edit_hahmon.py
```

## Environment

This is developed and tested on several Debian and related Linux distros
including Debian 9 and 10, Ubuntu 16.04 and Raspbian Stretch. The project
uses Python3 and the SQLite database.

## Requirements

* Mosquitto package client. (`apt install mosquitto-clients` on Debian and related distros.)
* Program to report exceptions `sa.sh`. One I use is

```shell
#!/bin/sh

# Script to send alarm notifications to gmail
# if email is properly configured as described in
# https://docs.google.com/document/d/1h9UxAvgpKXoCM8M3NzPOx3VvoNyjTwO5lbxIBvrIq9c/

# usage 'echo "message to send" | sa.sh "subject"

# bugs - will hang if nothing is sent to STDIN (perhaps die if run from another script)

mail -s "$1" root
```