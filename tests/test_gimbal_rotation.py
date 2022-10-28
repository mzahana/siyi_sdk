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

    val = cam.getGimbalAttitude()
    if val is not None:
        y,p,r,y_s,p_s,r_s = val
        print("Camera yaw_deg ", y)
        print("Camera pitch_deg ", p)
        print("Camera roll_deg ", r)

        print("Camera yaw speed deg/s ", y_s)
        print("Camera pitch speed deg/s ", p_s)
        print("Camera roll speed deg/s ", y_s)
    else:
        print("ERROR. Could not get gimbal attitude")

    sleep(1)

    yaw =10 # -45~45 degrees
    pitch=-90 # -90~25 degrees
    print("Setting gimbal rotation, yaw= {}, pitch= {}".format(yaw,pitch))
    val = cam.setGimbalRotation(yaw, pitch)

if __name__ == "__main__":
    test()