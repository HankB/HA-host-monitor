    def test_update_host_activity(self):
        # muck about with time.time() as described in
        # https://stackoverflow.com/questions/2658026/how-to-change-the-date-time-in-python-for-all-modules/
        # "(monkey-patching)"
        current_time=int(time.time())
        time_time = time.time
        bias = 0              # apply a bias of 0 seconds
        def mytime(): return current_time + bias
        time.time = mytime

        edit_hahmon.create_database(test_DB_name)
        edit_hahmon.insert_host(test_DB_name, "oak", 300)
        edit_hahmon.insert_host(test_DB_name, "oak", 500, "/some/topic")

        bias = 1000              # apply a bias of 1000 seconds

        self.assertEqual(edit_hahmon.update_host_activity(test_DB_name,
                "home_automation/oak/roamer/outside_temp_humidity \
                1536080280, 92.36, 58.06"), 0, "update timestamp")
        self.validate_record("oak",current_time+bias,300)
        self.validate_record("oak",current_time,500, "/some/topic")
        
        bias = 2000              # apply a bias of 1000 seconds

        self.assertEqual(edit_hahmon.update_host_activity(test_DB_name,
                "/some/topic \
                1536080280, 92.36, 58.06"), 0, "update timestamp")
        self.validate_record("oak",current_time+1000,300)
        self.validate_record("oak",current_time+bias,500, "/some/topic")
        

        time.time=time_time     # un-muck time.time()
        # comment next line to allow manual examination of database
        # pathlib.Path.unlink(pathlib.Path(test_DB_name))


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
        match_result = host_match(c, host, topic)
        if match_result == 1: # host/topic found
            c.execute('''update host_activity set timestamp=?
                    where host=? and topic=?''', (int(time.time()), host, topic,))
            conn.commit()
            rc = 0
        elif match_result == 0: # no match on host/topic
            print("no match host/topic")
            match_result = host_match(c, host, None) # see if host with no topic exists
            if match_result == 1:   # host/None matched
                c.execute('''update host_activity set timestamp=?
                        where host=? and topic is NULL''', (int(time.time()), host, ))
                conn.commit()
                rc = 0
            elif match_result == 0: # still not found
                print("no match host/None")
                rc = 1
            else:
                rc = 2
        else:
            print("host_match()", match_result)
            rc = 2
    except:
        print("DB Exception")
        rc = 2
    finally:
        c.close()

    return rc
