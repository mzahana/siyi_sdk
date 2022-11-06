#!/bin/env/python3
"""
RTSP client for getting video stream from SIYI cameras, e.g. ZR10, A8 Mini
ZR10 webpage: http://en.siyi.biz/en/Gimbal%20Camera/ZR10/overview/
A8 mini page: https://shop.siyi.biz/products/siyi-a8-mini?VariantsId=10611
Author : Mohamed Abdelkader
Email: mohamedashraf123@gmail.com
Copyright 2022

Required:
- OpenCV
    (sudo apt-get install python3-opencv -y)
- imutils
    pip install imutils
- Gstreamer (https://gstreamer.freedesktop.org/documentation/installing/index.html?gi-language=c)
    (Ubuntu: sudo apt-get install libgstreamer1.0-dev libgstreamer-plugins-base1.0-dev libgstreamer-plugins-bad1.0-dev gstreamer1.0-plugins-base gstreamer1.0-plugins-good gstreamer1.0-plugins-bad gstreamer1.0-plugins-ugly gstreamer1.0-libav gstreamer1.0-doc gstreamer1.0-tools gstreamer1.0-x gstreamer1.0-alsa gstreamer1.0-gl gstreamer1.0-gtk3 gstreamer1.0-qt5 gstreamer1.0-pulseaudio -y)
- Deepstream (only for Nvidia Jetson boards)
    (https://docs.nvidia.com/metropolis/deepstream/dev-guide/text/DS_Quickstart.html#jetson-setup)
- For RTMP streaming
    sudo apt install ffmpeg -y
    pip install ffmpeg-python
"""
import cv2
from imutils.video import VideoStream
import logging
from time import time, sleep
import subprocess
import threading


class SIYIRTSP:
    def __init__(self, rtsp_url="rtsp://192.168.144.25:8554/main.264", cam_name="ZR10", debug=False) -> None:
        '''
        Receives video stream from SIYI cameras

        Params
        --
        - rtsp_url [str] RTSP url
        - cam_name [str] camera name (optional)
        - debug [bool] print debug messages
        '''
        self._rtsp_url=rtsp_url

        self._cam_name=cam_name

        # Desired image width/height
        self._width=1280
        self._height=720

        # Stored image frame
        self._frame=None

        self._debug= debug # print debug messages
        if self._debug:
            d_level = logging.DEBUG
        else:
            d_level = logging.INFO
        LOG_FORMAT=' [%(levelname)s] %(asctime)s [SIYIRTSP::%(funcName)s] :\t%(message)s'
        logging.basicConfig(format=LOG_FORMAT, level=d_level)
        self._logger = logging.getLogger(self.__class__.__name__)

        # Flad to stop frame grapping loop, and close windows
        self._stopped=False

        # Show grapped frame in a window (mainly for debugging)
        self._show_window=False

        self._last_image_time=time()

        # timeout (seconds) before closing everything
        # If the returned frame is None for this amount of time, exit
        self._connection_timeout=2.0

        # Image receiving thread
        self._recv_thread = threading.Thread(target=self.loop)

        # start stream
        self.start()

    def setShowWindow(self, f: bool):
        self._show_window=f

    def getFrame(self):
        """
        Returns current image frame
        """
        return(self._frame)

    def start(self):
        """
        Start receiving thread
        """
        try:
            self._logger.info("Connecting to %s...", self._cam_name)
            self._stream = VideoStream(self._rtsp_url).start()
            self._recv_thread.start()
            self._stopped=False
        except Exception as e:
            self._logger.error(" Could not receive stream from %s. Error %s", self._cam_name, e)
            exit(1)
        
    def close(self):
        self._logger.info("Closing stream of %s...", self._cam_name)
        cv2.destroyAllWindows()
        self._stream.stop()
        self._stopped=True

    def loop(self):
        self._last_image_time=time()
        while not self._stopped:
            self._logger.debug("Reading frame form %s ...", self._cam_name)
            self._frame = self._stream.read()

            if (time()-self._last_image_time)> self._connection_timeout:
                self._logger.warning("Connection timeout. Exiting")
                self.close()
            
            if self._frame is None:
                continue

            self._last_image_time=time()

            # self._frame = imutils.resize(frame, width=self._width, height=self._height)


            if self._show_window:
                cv2.imshow('{} Stream'.format(self._cam_name), self._frame)
                
                key = cv2.waitKey(25) & 0xFF

                if key == ord('q'):
                    self.close()
                    break

        self._logger.warning("RTSP receiving loop is done")
        return

class RTMPSender:
    '''
    Streams image frames to an RTMP server
    '''
    def __init__(self, rtmp_url="rtmp://127.0.0.1:1935/live/webcam", debug=False) -> None:
        '''
        Params
        --
        - rtmp_url [str] RTMP server URL
        - debug [bool] Printing debug message
        '''
        self._rtmp_url=rtmp_url
        # Desired frequency of streaming to rtmp server
        self._fps =30

        self._last_send_time = time()
        self._current_send_time = time()


        # Frame to send
        self._frame = None

        # Desired image height
        self._height = 480
        # Desired image width
        self._width = 640

        self._toGray=False
        if self._toGray:
            self._pix_fmt="gray"
        else:
            self._pix_fmt="bgr24"

        # Flag to stop streaming loop
        self._stopped = False

        self._debug= debug # print debug messages
        if self._debug:
            d_level = logging.DEBUG
        else:
            d_level = logging.INFO
        LOG_FORMAT=' [%(levelname)s] %(asctime)s [RTMPSender::%(funcName)s] :\t%(message)s'
        logging.basicConfig(format=LOG_FORMAT, level=d_level)
        self._logger = logging.getLogger(self.__class__.__name__)

        # Streaming thread
        self._st_thread = threading.Thread(target=self.loop)

        
    def setImageSize(self, w=640, h=480):
        self._width=w
        self._height=h

    def setFPS(self, fps=20):
        self._fps=fps

    def setGrayFrame(self, b: bool):
        '''
        Params
        --
        - b [bool] True: sends grayscale image. Otherwise sends color image
        '''
        self._toGray = b
        if self._toGray:
            self._pix_fmt="gray"
        else:
            self._pix_fmt="bgr24"


    def setFrame(self, frame):
        self._frame=frame


    def start(self):
        command = ["ffmpeg",
            "-y",
            "-f", "rawvideo",
            "-vcodec", "rawvideo",
            "-pix_fmt", self._pix_fmt,
            "-s", "{}x{}".format(self._width, self._height),
            "-r", str(self._fps),
            "-i", "-",
            "-c:v", "libx264",
            '-pix_fmt', 'yuv420p',
            "-preset", "ultrafast",
            "-f", "flv",
            "-tune", "zerolatency",
            self._rtmp_url]
        # using subprocess and pipe to fetch frame data
        try:
            self._p = subprocess.Popen(command, stdin=subprocess.PIPE)
        except Exception as e:
            self._logger.error("Could not create ffmpeg pipeline. Error %s", e)
            exit(1)

        try:
            self._st_thread.start()
        except Exception as e:
            self._logger.error("Could not start RTMP streaming thread")
            exit(1)

    def stop(self):
        """
        Stops streaming thread
        """
        self._logger.warning("RTMP streaming is stopped.")
        self._stopped=True
        self._p.kill()

    def sendFrame(self) -> bool:
        '''
        Sends current image frame stored in self._frame

        Returns
        --
        True if all is fine. False otherwise
        '''
        if self._frame is None:
            return False

        try:
            val = self._frame.shape
            rows = val[0]
            cols=val[1]
            # Resize the image, if needed
            if rows != self._height or cols != self._width:
                self._frame = cv2.resize(self._frame, (self._width,self._height), interpolation = cv2.INTER_AREA)

            if self._toGray and (len(self._frame.shape) > 2):
                self._frame = cv2.cvtColor(self._frame, cv2.COLOR_BGR2GRAY)

            self._p.stdin.write(self._frame.tobytes())

            return(True)
        except Exception as e:
            self._logger.error(" Error in sending:  %s", e)
            return(False)

    def loop(self):
        while(not self._stopped):
            dt = time() - self._last_send_time
            start_t=time()
            self.sendFrame()
            end_t=time()
            dt=end_t-start_t
            duration = 1/self._fps
            if  dt < duration:
                sleep(duration-dt)

        self._logger.warning("RTMP streaming loop is done")
        return

        


def test():
    # rtsp = SIYIRTSP(debug=False)
    # rtsp.setShowWindow(True)
    # Webcam
    try:
        wc = VideoStream(src=0).start()
    except Exception as e:
        print("Error in opening webcam")
        exit(1)

    rtmp = RTMPSender(rtmp_url="rtmp://127.0.0.1:1935/live/webcam")
    rtmp.start()
    try:
        while(True):
            # frame=stream.getFrame()
            frame=wc.read()
            rtmp.setFrame(frame)
    except KeyboardInterrupt:
        # rtsp.close()
        rtmp.stop()
        wc.stop()
        cv2.destroyAllWindows()
        # quit
        exit(0)

    

if __name__=="__main__":
    test()
