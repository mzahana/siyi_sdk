
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
    req_stream_type = 1 # 0: recording stream, 1: main stream, 2: sub stream
    print(f"Requesting current codec specs for stream type {req_stream_type}: ", cam.requestGimbalCameraCodecSpecs(req_stream_type))
    sleep(1)
    stream_type, video_enc_type, resolution_l, resolution_h, video_bitrate, video_framerate = cam.getGimbalCameraCodecSpecs()
    print(f"Stream type: {stream_type}, Video encoding type: {video_enc_type}, Resolution: {resolution_l}x{resolution_h}, Video bitrate: {video_bitrate} kbps, Video framerate: {video_framerate} fps")
    sleep(1)
    print()



    stream_type = 1 # 0: recording stream, 1: main stream, 2: sub stream
    video_enc_type = 1 # 1: H.264 or 2: H.265
    resolution_l = 1920 # 1920 or 1280
    resolution_h = 1080 # 1080 or 720
    video_bitrate = 2999 # 0-3000 kbps
    print(f"Setting codec specs to:")
    print(f"Stream type: {stream_type}, Video encoding type: {video_enc_type}, Resolution: {resolution_l}x{resolution_h}, Video bitrate: {video_bitrate} kbps")
    val = cam.sendGimbalCameraCodecSpecs(stream_type, video_enc_type, resolution_l, resolution_h, video_bitrate)
    print(f"Success?: {val}")
    sleep(2)



    print()
    req_stream_type = 1 # 0: recording stream, 1: main stream, 2: sub stream
    print(f"Requesting current codec specs for stream type {req_stream_type}: ", cam.requestGimbalCameraCodecSpecs(req_stream_type))
    sleep(1)
    stream_type, video_enc_type, resolution_l, resolution_h, video_bitrate, video_framerate = cam.getGimbalCameraCodecSpecs()
    print(f"Stream type: {stream_type}, Video encoding type: {video_enc_type}, Resolution: {resolution_l}x{resolution_h}, Video bitrate: {video_bitrate} kbps, Video framerate: {video_framerate} fps")
    sleep(1)
    print()
    cam.disconnect()

if __name__ == "__main__":
    test()
