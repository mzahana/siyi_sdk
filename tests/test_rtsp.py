"""
@file test_rtsp.py
@Description: Test receiving RTSP stream from IP camera
@Author: Mohamed Abdelkader
@Contact: mohamedashraf123@gmail.com
All rights reserved 2022
"""

import sys
import os
from imutils.video import VideoStream
from time import sleep
  
current = os.path.dirname(os.path.realpath(__file__))
parent_directory = os.path.dirname(current)
  
sys.path.append(parent_directory)

from stream import SIYIRTSP

def test():
    rtsp = SIYIRTSP(rtsp_url="rtsp://192.168.144.25:8554/main.264",debug=False)
    rtsp.setShowWindow(True)
if __name__ == "__main__":
    test()