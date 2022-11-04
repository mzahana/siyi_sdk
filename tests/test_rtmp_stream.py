"""
@file test_rtmp_stream.py
@Description: Test sending webcam image frames to an RTMP server
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

from stream import RTMPSender

def test():
    # Webcam
    try:
        # Assuming the webcam /dev/video0
        # Change according to your webcam source
        wc = VideoStream(src=0).start()
        print("Connected to webcam.")
        sleep(2)
    except Exception as e:
        print("Error in opening webcam. Exit...")
        exit(1)
    
    rtmp = RTMPSender(rtmp_url="rtmp://127.0.0.1:1935/live/webcam")
    rtmp.setFPS(20)
    rtmp.setGrayFrame(False)
    rtmp.setImageSize(320,240)
    print("Starting RTMP stream...")
    sleep(1)
    rtmp.start()

    try:
        while(True):
            frame=wc.read()
            rtmp.setFrame(frame)
    except KeyboardInterrupt:
        rtmp.stop()
        wc.stop()
        
        # quit
        exit(0)

if __name__ == "__main__":
    test()