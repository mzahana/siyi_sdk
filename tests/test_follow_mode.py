"""
@file test_follow_mode.py
@Description: This is a test script for using the ZR10 SDK Python implementation to set follow mode
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

    val = cam.setFollowMode()
    print("Setting Foloow mode: ", val)

if __name__ == "__main__":
    test()