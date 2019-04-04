#!/usr/bin/env python3

"""
Test program for edit_hahmon (Home Automation Host Monitor)
"""

import hahmon
# import edit_hahmon
import unittest

# example data
msgs = [
    '''home_automation/brandywine/roamer/outside_temp_humidity 1553831160, 47.54, 76.44
home_automation/sodus/master_bedroom/temp_humidity 1553831160, 72.50, 30.98
home_automation/haut/dining_room/temp_humidity 1553831160, 72.69, 37.52
home_automation/latham/dining_room_W/temp_humidity 1553831161, 70.93, 30.95
home_automation/skeena/garage_eave/outside_temp_humidity 1553831161, 49.87, 61.56
'''
]


class UpdateHAmonTest(unittest.TestCase):

    def test_parse_MQTT_msg(self):
        rc = hahmon.parse_MQTT_msg(
            'ha/brandywine/roamer/outside_temp_humidity 1553831160, 47.54, 76.44')
        self.assertEqual(
            rc, ('brandywine', '/roamer/outside_temp_humidity', 1553831160),
                        "parse_MQTT_msg()")

        # test invalid argument
        with self.assertRaises(SystemExit, msg="exit on [-x]"):
            hahmon.parse_args(['-x'])


if __name__ == "__main__":
    unittest.main()
