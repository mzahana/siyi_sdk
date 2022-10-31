"""
@file test_gimbal_rotation.py
@Description: This is a test script for using the SIYI SDK Python implementation to set/get gimbal rotation
@Author: Mohamed Abdelkader
@Contact: mohamedashraf123@gmail.com
All rights reserved 2022
"""

from time import sleep
import sys
import os
  
current = os.path.dirname(os.path.realpath(__file__))
parent_directory = os.path.dirname(current)
  
sys.path.append(parent_directory)

from siyi_sdk import SIYISDK

def test():
    cam = SIYISDK(server_ip="192.168.144.25", port=37260)
    if not cam.connect():
        print("No connection ")
        exit(1)

    cam.setGimbalRotation(10,-50)

    print("Attitude (yaw,pitch,roll) eg:", cam.getAttitude())
    
    cam.disconnect()

if __name__ == "__main__":
    test()