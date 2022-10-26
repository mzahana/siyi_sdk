"""
@file test_get_hw_id.py
@Description: This is a test script for using the ZR10 SDK Python implementation to get hardware ID
@Author: Mohamed Abdelkader
@Contact: mohamedashraf123@gmail.com
All rights reserved 2022
"""

from zr10_python import ZR10SDK

def test():
    cam = ZR10SDK(server_ip="192.168.144.25", port=37260)

    val = cam.getHardwareID()

    print("Camera hardware ID: ", val)

if __name__ == "__main__":
    test()