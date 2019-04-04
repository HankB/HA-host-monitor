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

## Reliability of Broker Connection

Due to the nature of this task, it is of upmost importance that the connection
to the broker be absolutely reliable. It must recover from the following
conditions:

* Loss of network connectivity on the client
* loss of network connectivity on the broker host
* reboot of broker host
* shutdown and restart of broker service

Initial testing with `mosquitto_sub` indicates it reliably performs this function.
With some additional logic the `paho-mqtt` module can do this as well.

## Components

1. Process to create and edit database entries.
1. Process to handle incoming MQTT messages and update the database.
1. Process to scan the database and look for overdue hosts.
1. Test script(s) to test portions of the various other components.

## Files

(It's a pain to come back after several months and not be able to figure out where I was.)

```test
edit_hahmon.py          create and update database.
test_edit_hahmon.py     unit tests for edit_hahmon.py
hahmon.py               Common functionality shared by paho_hahmon.py (as yet not coded) mosquitto_hahmon.py)
paho_hahmon.py          Code to receive MQTT messages using module paho-mqtt to subscribe.
test_hahmon.py          unittest for hahmon.py, paho_hahmon.py specific code.
update_hahmon.py        ? holds presently unused code?
```

## Status

`paho_hahmon.py` subscribed to MQTT server and reports messages to console.
Will perform some testing with this to see what happens when network or
broker cannot be reached or lose an already established connection. See
"Reliability of Broker Connection" above.

## Testing

```bash
./test_edit_hahmon.py
./test_edit_hahmon.py UpdateHAmonTest.test_create_database
./test_edit_hahmon.py UpdateHAmonTest.test_parse_args 2>/dev/null
./test_hahmon.py
```

## Environment

This is developed and tested on several Debian and related Linux distros
including Debian 9 and 10, Ubuntu 16.04 and Raspbian Stretch. The project
uses Python3 and the SQLite database.

## Requirements

* Mosquitto package client. (`apt install mosquitto-clients` on Debian and related distros.)

or

* Python paho-mqtt module (`pip3 install paho-mqtt` on Debian Stretch)
* `sqlite3` (`apt install sqlite3` )
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