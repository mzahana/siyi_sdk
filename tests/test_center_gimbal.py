"""
@file test_center_gimbal.py
@Description: This is a test script for using the SIYI SDK Python implementation to bring the gimbal to center position
@Author: Mohamed Abdelkader
@Contact: mohamedashraf123@gmail.com
All rights reserved 2022
"""

import sys
import os
  
current = os.path.dirname(os.path.realpath(__file__))
parent_directory = os.path.dirname(current)
  
sys.path.append(parent_directory)

from siyi_sdk import SIYISDK

def test():
    cam = SIYISDK(server_ip="192.168.144.25", port=37260)

    val = cam.centerGimbal()

    print("Centering gimbal: ", val)

if __name__ == "__main__":
    test()