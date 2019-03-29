#!/usr/bin/env python3

"""
Test program for edit_hahmon (Home Automation Host Monitor)
"""

import edit_hahmon
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
