import tkinter as tk
from tkinter import ttk
from tkinter import filedialog as fd
from tkinter.messagebox import showinfo

from time import sleep
import sys
import os
  
current = os.path.dirname(os.path.realpath(__file__))
parent_directory = os.path.dirname(current)
  
sys.path.append(parent_directory)

from siyi_sdk import SIYISDK

# create the window window
window = tk.Tk()
window.title('SiYi Ground Control ( ͡❛ ͜ʖ ͡❛)')
# window.resizable(False, False)
window.geometry('320x240')

class CamAngle:
    def __init__(self):
        self.yaw = 0
        self.pitch = 0

    def addYaw(self, dy):
        self.yaw += dy
        if self.yaw >45:
            self.yaw = 45
        if self.yaw <-45:
            self.yaw = -45

    def addPitch(self, dp):
        self.pitch += dp
        if self.pitch >25:
            self.pitch = 25
        if self.pitch <-90:
            self.pitch = -90


    def zeroYaw(self):
        self.yaw = 0

    def zeroPitch(self):
        self.pitch = 0

cam_angle = CamAngle()

cam = SIYISDK(server_ip="192.168.144.25", port=37260)
if not cam.connect():
    print("No connection ")
    exit(1)


cam.requestFollowMode()

def pitch_up():
    cam_angle.addPitch(5)
    cam.setGimbalRotation(cam_angle.yaw, cam_angle.pitch)
    # cam.setGimbalRotation(0,10)
    print("Attitude (yaw,pitch,roll) eg:", cam.getAttitude())

# pitch up button
pitch_up_button = ttk.Button(
    window,
    text='🢁',
    command=pitch_up
)

pitch_up_button.grid(row = 0, column = 1, pady = 2)

# pitch_up_button.pack(expand=True)


def pitch_down():
    cam_angle.addPitch(-5)
    cam.setGimbalRotation(cam_angle.yaw, cam_angle.pitch)
    # cam.setGimbalRotation(0,10)
    print("Attitude (yaw,pitch,roll) eg:", cam.getAttitude())

# pitch down button
pitch_down_button = ttk.Button(
    window,
    text='🢃',
    command=pitch_down
)

pitch_down_button.grid(row = 2, column = 1, pady = 2)
# pitch_down_button.pack(expand=True)


def yaw_left():
    cam_angle.addYaw(5)
    cam.setGimbalRotation(cam_angle.yaw, cam_angle.pitch)
    # cam.setGimbalRotation(0,10)
    print("Attitude (yaw,pitch,roll) eg:", cam.getAttitude())

# pitch down button
yaw_left_button = ttk.Button(
    window,
    text='🢀',
    command=yaw_left
)

yaw_left_button.grid(row = 1, column = 0, pady = 2)
# yaw_left_button.pack(expand=True)


def yaw_right():
    cam_angle.addYaw(-5)
    cam.setGimbalRotation(cam_angle.yaw, cam_angle.pitch)
    # cam.setGimbalRotation(0,10)
    print("Attitude (yaw,pitch,roll) eg:", cam.getAttitude())

# pitch down button
yaw_right_button = ttk.Button(
    window,
    text='🢂',
    command=yaw_right
)

yaw_right_button.grid(row = 1, column = 2, pady = 2)
# yaw_right_button.pack(expand=True)


# 🎯

def picth_yaw_center():
    cam_angle.zeroYaw()
    cam_angle.zeroPitch()
    cam.setGimbalRotation(cam_angle.yaw, cam_angle.pitch)
    # cam.setGimbalRotation(0,10)
    print("Attitude (yaw,pitch,roll) eg:", cam.getAttitude())

# pitch down button
picth_yaw_center_button = ttk.Button(
    window,
    text='🎯',
    command=picth_yaw_center
)

picth_yaw_center_button.grid(row = 1, column = 1, pady = 2)
# picth_yaw_center_button.pack(expand=True)


# 🔎 ➕

def zoom_in():
    val = cam.requestZoomIn()
    sleep(0.5)
    val = cam.requestZoomHold()
    sleep(0.5)
    print("Zoom level: ", cam.getZoomLevel())

# pitch down button
zoom_in_button = ttk.Button(
    window,
    text='🔎➕',
    command=zoom_in
)

zoom_in_button.grid(row = 3, column = 0, pady = 2)
# zoom_in_button.pack(expand=True)


# 🔎 ➖ 

def zoom_out():
    val = cam.requestZoomOut()
    sleep(0.5)
    val = cam.requestZoomHold()
    sleep(0.5)
    print("Zoom level: ", cam.getZoomLevel())

# pitch down button
zoom_out_button = ttk.Button(
    window,
    text='🔎➖',
    command=zoom_out
)

zoom_out_button.grid(row = 3, column = 2, pady = 2)
# zoom_out_button.pack(expand=True)


# run the application
window.mainloop()
cam.disconnect()
print("exit")
