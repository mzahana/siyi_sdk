"""
@file test_center_gimbal.py
@Description: This is a test script for using the SIYI SDK Python implementation to adjust zoom level
@Author: Mohamed Abdelkader
@Contact: mohamedashraf123@gmail.com
All rights reserved 2022
"""

import sys
import os
from time import sleep
  
current = os.path.dirname(os.path.realpath(__file__))
parent_directory = os.path.dirname(current)
  
sys.path.append(parent_directory)

from siyi_sdk import SIYISDK

def test():
    cam = SIYISDK(server_ip="192.168.144.25", port=37260)

    if not cam.connect():
        print("No connection ")
        exit(1)

    x = 100
    y = 100
    get_temp_flag = 1
    print(f"Requesting temperature at point ({x}, {y})")
    cam.requestTemperatureAtPoint(x, y, get_temp_flag)
    sleep(2)
    temp, x, y = cam.getTemperatureAtPoint()

    print(f"Temperature: {temp}, X: {x}, Y: {y}")
    sleep(3)

    cam.disconnect()

if __name__ == "__main__":
    test()