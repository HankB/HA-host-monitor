#!/usr/bin/env python3
'''
Monitor hosts 
Read output of mosquitto_sub
e.g. `mosquitto_sub -v -h oak -t \#`
Process all messages and update the database according to 
the incoming messages.
'''

import re


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
