#!/usr/bin/python3
"""
Subscribe to the MQTT server used for home automation and


Modified from recorder.py in ssh://git@oak:10022/HankB/home_automation-MQTT-recorder.git
since there is a *lot* of overlap in functionality. This variant subscribes
to the messages and updates the host monitor database. Following the convention
used by edit_hahmon.py and use the environment variable to identify the database

store
all messages received. Messages themselves are in the form
"<timestamp>, <rest of payload>"
In addition to these fields, the topic for each message will be stored also.
The topic includes the host name as the second field. For example:
    topic: "home_automation/niwot/basement/freezer_temp"
    payload: "1510537800, 12.8



"""
import sqlite3
import atexit
import re
import os
import time

# db_name = 'home_automation-MQTT.db'


def close_connection(some_con):
    some_con.commit()
    some_con.close()

'''
conn = sqlite3.connect(db_name)
atexit.register(close_connection, conn)
c = conn.cursor()
'''
'''
Parse the topic and payload to extract host, rest of topic and timestamp.
e g for
    topic 'home_automation/sodus/master_bedroom/temp_humidity'
    payload '1553884981, 70.95, 29.16'
return ('sodus', '/master_bedroom/temp_humidity', 1553884981)
'''


def parse_mqtt_msg(topic, payload):
    topic = re.split('\W+', topic)  # now split on space, comma
    host = topic[1]
    topic = '/' + topic[2] + '/' + topic[3]
    payload = re.split('\W+', payload)  # now split on space, comma
    timestamp = int(payload[0])
    return (host, topic, timestamp)

# copied from https://www.eclipse.org/paho/clients/python/
import paho.mqtt.client as mqtt

# The callback for when the client receives a CONNACK response from the server.


def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))
    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    # client.subscribe("$SYS/#")

# The callback for when a PUBLISH message is received from the server.


def on_message(client, userdata, msg):
    # payload=str(msg.payload)
    payload = msg.payload.decode("utf-8")
    print("payload \'" + payload + '\'')
    print("topic \'" + msg.topic + '\'')
    print(parse_mqtt_msg(msg.topic, payload))
    print()
    # print(msg.topic+" "+payload)
    #(root, host, location, description) = msg.topic.split('/')
    # print("topic fields", root, host, location, description)
    '''
    fields = msg.topic.split('/')
    print(fields)
    if len(fields) != 4:
        print("Wrong number of levels in", msg.topic )
        host = location = description = "unk"
    else:
        host = fields[1]
        location = fields[2]
        description = fields[3]
    print("topic fields", host, location, description)
    fields = payload.split(',', 1)
    if len(fields) != 2:
        print("malformed payload", payload)
        ts = 0
        value = payload
    else:
        print("payload fields", fields)
        ts = int(fields[0])
        value = fields[1]
    print("payload decoded", ts, value)
    insert_data(ts, host, location, description, value)
    '''


def on_publish(client, userdata, mid):
    print("on_publish(", client, userdata, mid, ")")


def on_subscribe(client, userdata, mid, granted_qos):
    print("on_subscribe()")

'''
def insert_data(timestamp, host, location, description, payload):
    sql = '' ' INSERT INTO messages(timestamp,host,location,description,payload)
              VALUES(?,?,?,?,?) '' '
    c.execute(sql, (timestamp, host, location, description, payload))
    conn.commit()
'''


def paho_hahmon_main():

    hamon_db = os.environ.get('DB_NAME_ENV')
    if hamon_db is None:
        print('Please specify the database location')
        print('e.g. \'export  DB_NAME_ENV=path/to/database\'')
        exit(1)

    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    while(1):
        try:
            client.connect("contorta", 1883, 60)  # connect to my MQTT server

            client.subscribe("#")   # subscribe to everything for now
            # Blocking call that processes network traffic, dispatches callbacks and
            # handles reconnecting.
            # Other loop*() functions are available that give a threaded interface and a
            # manual interface. (changed to non-blocking call)
            while(1):
                client.loop()
            # end of included code
            print("finished loop")  # Shouldn't get here, no?

        except Exception as Argument:
            print("Exception", Argument)
            time.sleep(5)


paho_hahmon_main()
