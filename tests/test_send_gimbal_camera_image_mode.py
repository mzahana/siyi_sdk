"""
@file test_request_gimbal_camera_image_mode.py
@Description: This is a test script for using the SIYI SDK Python implementation to request gimbal camera image mode
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

    print()
    print("Requesting gimbal camera image mode...")
    cam.requestGimbalCameraImageMode()
    sleep(1)
    print(f"Current gimbal camera image mode: {cam.getGimbalCameraImageMode()}")
    print()

    
    """
    image_mode_map = {
                0: "Split Screen (Main: Zoom & Thermal. Sub: Wide Angle)",
                1: "Split Screen (Main: Wide Angle & Thermal. Sub: Zoom)",
                2: "Split Screen (Main: Zoom & Wide Angle. Sub: Thermal)",
                3: "Single Images (Main: Zoom. Sub: Thermal)", # THIS IS THE BEST MODE FOR US!!
                4: "Single Images (Main: Zoom. Sub: Wide Angle)",
                5: "Single Images (Main: Wide Angle. Sub: Thermal)",
                6: "Single Images (Main: Wide Angle. Sub: Zoom)",
                7: "Single Images (Main: Thermal. Sub: Zoom)",
                8: "Single Images (Main: Thermal. Sub: Wide Angle)",
            }
    """
    image_mode = 3
    print(f"Sending gimbal camera image mode: {image_mode}")
    print(cam.sendGimbalCameraImageMode(image_mode))
    sleep(5)
    print()

    cam.requestGimbalCameraImageMode()
    print(f"Current gimbal camera image mode: {cam.getGimbalCameraImageMode()}")
    print()
    cam.disconnect()

if __name__ == "__main__":
    test()
