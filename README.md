# siyi_sdk
Python implementation of SIYI SDK for communication with ZR10 and A8 Mini cameras


* Camera webpage: http://en.siyi.biz/en/Gimbal%20Camera/ZR10/overview/
* Documentation: http://en.siyi.biz/en/Gimbal%20Camera/ZR10/download/

**If you find this code useful, kindly give a STAR to this repository. Thanks!**

# Setup
* Clone this package
    ```bash
    git clone https://github.com/mzahana/siyi_sdk.git
    ```
* Connect the camera to PC or onboard computer using the ethernet cable that comes with it. The current implementation uses UDP communication.
* Power on the camera
* Do the PC wired network configuration. Make sure to assign a manual IP address to your computer
  * For example, IP `192.168.144.12`
  * Gateway `192.168.144.25`
  * Netmask `255.255.255.0`
* Done. 

# Usage
* Check the scripts in the `siyi_sdk/tests` directory to learn how to use the SDK

* To import this module in your code, copy the `siyi_sdk.py` `siyi_message.py` `utility.py` `crc16_python.py` scripts in your code directory, and import as follows, and then follow the test examples
    ```python
    from siyi_sdk import SIYISDK
    ```
* Example: To run the `test_gimbal_rotation.py` run,
    ```bash
    cd siyi_sdk/tests
    python3 test_gimbal_rotation.py
    ```
# Video Streaming
## Requirements
* OpenCV `sudo apt-get install python3-opencv -y`
* imutils `pip install imutils`
* Gstreamer `https://gstreamer.freedesktop.org/documentation/installing/index.html?gi-language=c`
    
    Ubuntu:
    ```bash
    sudo apt-get install libgstreamer1.0-dev libgstreamer-plugins-base1.0-dev libgstreamer-plugins-bad1.0-dev gstreamer1.0-plugins-base gstreamer1.0-plugins-good gstreamer1.0-plugins-bad gstreamer1.0-plugins-ugly gstreamer1.0-libav gstreamer1.0-doc gstreamer1.0-tools gstreamer1.0-x gstreamer1.0-alsa gstreamer1.0-gl gstreamer1.0-gtk3 gstreamer1.0-qt5 gstreamer1.0-pulseaudio -y
    ```
- Deepstream (only for Nvidia Jetson boards)
    (https://docs.nvidia.com/metropolis/deepstream/dev-guide/text/DS_Quickstart.html#jetson-setup)
- For RTMP streaming
    ```bash
    sudo apt install ffmpeg -y
    pip install ffmpeg-python
    ```

## Examples
* An example of how to image frames from camera, see `tests/test_rtsp.py`
* An example of how to stream image frame to an RTMP server, see `tests/test_rtmp_stream.py`
* An example of how to receive an image stream from camera using RTSP and send them to an RTMP server, see `tests/test_from_rtsp_to_rtmp.py`