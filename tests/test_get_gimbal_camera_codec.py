
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

    print(f"Requesting current codec specs")
    req_stream_type = 1 # 0: recording stream, 1: main stream, 2: sub stream
    val = cam.requestGimbalCameraCodecSpecs(req_stream_type)
    print(f"Request codec specs status: {val}")
    sleep(2)

    stream_type, video_enc_type, resolution_l, resolution_h, video_bitrate, video_framerate = cam.getGimbalCameraCodecSpecs()
    print(f"Stream type: {stream_type}, Video encoding type: {video_enc_type}, Resolution: {resolution_l}x{resolution_h}, Video bitrate: {video_bitrate} kbps, Video framerate: {video_framerate} fps")
    sleep(1)

    cam.disconnect()

if __name__ == "__main__":
    test()
