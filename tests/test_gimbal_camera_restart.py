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

    camera_reboot = 1 # 0: No action, 1: Camera restart
    gimbal_reboot = 1 # 0: No action, 1: Gimbal restart
    print(f"Requesting gimbal camera soft restart")
    val = cam.requestGimbalCameraSoftRestart(camera_reboot, gimbal_reboot)
    print(f"Request gimbal camera soft restart status: {val}")
    sleep(10)

    camera_reboot, gimbal_reboot = cam.getGimbalCameraSoftRestart()

    print(f"Camera reboot: {camera_reboot}, Gimbal reboot: {gimbal_reboot}")
    sleep(3)

    cam.disconnect()

if __name__ == "__main__":
    test()