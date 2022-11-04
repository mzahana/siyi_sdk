"""
@file test_from_rtsp_to_rtmp.py
@Description: Test receiving RTSP stream from IP camera and sending it to RTMP server
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

from stream import SIYIRTSP, RTMPSender

def test():
    rtsp = SIYIRTSP(rtsp_url="rtsp://192.168.144.25:8554/main.264",debug=False)
    rtsp.setShowWindow(True)

    rtmp = RTMPSender(rtmp_url="rtmp://127.0.0.1:1935/live/webcam")
    rtmp.start()

    try:
        while(True):
            frame=rtsp.getFrame()
            rtmp.setFrame(frame)
    except KeyboardInterrupt:
        rtsp.close()
        rtmp.stop()
        # quit
        exit(0)

if __name__ == "__main__":
    test()