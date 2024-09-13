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

    desired_zoom_level = 3.0
    print(f"Setting zoom level to {desired_zoom_level}")
    cam.requestAbsoluteZoom(desired_zoom_level)
    sleep(3)
    print(f"Zoom level: {cam.getCurrentZoomLevel()}")

    print("Setting zoom level to 1")
    cam.requestAbsoluteZoom(1.0)
    sleep(3)
    print(f"Zoom level: {cam.getCurrentZoomLevel()}")
    

    cam.disconnect()

if __name__ == "__main__":
    test()