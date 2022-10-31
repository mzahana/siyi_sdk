"""
@file test_record_video.py
@Description: This is a test script for using the SIYI SDK Python implementation to record video
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

    if (cam.getRecordingState()<0):
        print("Toggle recording")
        cam.requestRecording()
        sleep(5)

    if (cam.getRecordingState()==cam._record_msg.TF_EMPTY):
        print("TF card lsot is empty")

    if (cam.getRecordingState()==cam._record_msg.ON):
        print("Recording is ON. Sending requesdt to stop recording")
        cam.requestRecording()
        sleep(2)

    print("Recording state: ", cam.getRecordingState())

    cam.disconnect()

if __name__ == "__main__":
    test()