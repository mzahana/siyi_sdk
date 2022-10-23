"""
Python implementation of ZR10 SDK by SIYI
ZR10 webpage: http://en.siyi.biz/en/Gimbal%20Camera/ZR10/overview/
Author : Mohamed Abdelkader
Email: mohamedashraf123@gmail.com
Copyright 2022

Requirements:
crc16 module which is included with this package
- cd crc16-0.1.1
- python setup.py build
- sudo python setup.py install

"""

import socket
import crc16

class ZR10SDK:
    """
    Implementation of ZR10 SDK communication protocol
    """

    def __init__(self, server_ip="192.168.144.25", port=37260) -> None:
        """"
        Params
        --
        server_ip [str] IP address of the camera
        port: [int] UDP port of the camera
        """
        self._server_ip = server_ip
        self._port = port

        self._BUFF_SIZE=1024

        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._socket.settimeout(1) # 1 second timeout for recvfrom()

    def toHex(self, val, nbits):
        """
        Converts an integer to hexdecimal.
        Useful for negative integers where hex() doesn't work as expected
        """
        h = format((val + (1 << nbits)) % (1 << nbits),'x')
        if len(h)==1:
            h="0"+h
        return h

    def connect(self) -> bool:
        """
        Connects to the camera UDP server using self._server_ip and self._port

        Returns
        --
        True: if connection is established with no errors
        False: if connection is not established
        """
        pass
    def disconnect(self) -> None:
        """
        Disconnect UDP socket
        """
        pass

    def sendMsg(self, msg) -> None:
        """
        Sends a message to the camera

        Params
        --
        msg [str] Message to send
        """
        b = bytes.fromhex(msg)
        self._socket.sendto(b, (self._server_ip, self._port))

    def rcvMsg(self):
        data=None
        try:
            data,addr = self._socket.recvfrom(self._BUFF_SIZE)
        except Exception as e:
            print("Error: {}".format(e))
        return data

    def decodeMsg(self) -> None:
        """
        Decodes messages that are received on the rcv buffer, and updates the corresponding fields.
        """
        pass

    def calcCRC16(self, msg: str):
        """
        Calculates the two bytes CRC16, with swaped order, and returns them as a string
        """
        try:
            b = bytes.fromhex(msg)
            int_crc = crc16.crc16xmodem(b)
            str_crc = format(int_crc, 'x')
            # Make sure we get 4 characters
            if len(str_crc)==3:
                str_crc = "0"+str_crc
            c1 = str_crc[2:]
            c2 = str_crc[0:2]
            crc = c1+c2
            return crc
        except Exception as e:
            print("Error: {}".format(e))
            return None

    def encodeMsg(self, data_len, data, cmd_id):
        """
        Encodes a msg according to SDK protocol

        Returns
        --
        [str] Encoded msg. Empty string if crc16 is not successful
        """
        STX="5566" # Starting bytes in string 0x5566
        CTRL = "01"
        SEQ = "0000" # low byte on the left
        msg_front = STX+CTRL+data_len+SEQ+cmd_id+data
        crc = self.calcCRC16(msg_front)
        if crc is not None:
            msg = msg_front+crc
            return msg
        else:
            return ''

    def acquireFirmwareVersionMsg(self) -> str:
        """
        Prepares the Acquire Firmware Version message, and returns it as a string

        Returns
        --
        [str] encoded msg if available. Otherwise, returns empty string
        """
        data=""
        data_len = "0000"
        cmd_id = "01"
        return self.encodeMsg(data_len, data, cmd_id)


    def acquireHardwareIdMsg(self) -> str:
        """
        Prepares the Acquire Hardware ID message, and returns it as a string

        Returns
        --
        [str] encoded msg if available. Otherwise, returns empty string
        """
        data=""
        data_len = "0000"
        cmd_id = "02"
        return self.encodeMsg(data_len, data, cmd_id)

    def autoFocusMsg(self) -> str:
        """
        Prepares the Auto Focus message, and returns it as a string

        Returns
        --
        [str] encoded msg if available. Otherwise, returns empty string
        """
        data="01"
        data_len = "0100"
        cmd_id = "04"
        return self.encodeMsg(data_len, data, cmd_id)

    def stopZoomMsg(self, flag) -> str:
        """
        Prepares the Stop Zoom message, and returns it as a string

        Returns
        --
        [str] encoded msg if available. Otherwise, returns empty string
        """
        data="00"
        data_len = "0100"
        cmd_id = "05"
        return self.encodeMsg(data_len, data, cmd_id)

    def zoomInMsg(self) -> str:
        """
        Prepares the Manual Zoom In message, and returns it as a string

        Returns
        --
        [str] encoded msg if available. Otherwise, returns empty string
        """
        data="01"
        data_len = "0100"
        cmd_id = "05"
        return self.encodeMsg(data_len, data, cmd_id)

    def zoomOutMsg(self) -> str:
        """
        Prepares the Manual Zoom Out message, and returns it as a string

        Returns
        --
        [str] encoded msg if available. Otherwise, returns empty string
        """
        data="ff"
        data_len = "0100"
        cmd_id = "05"
        return self.encodeMsg(data_len, data, cmd_id)

    def manualFocusMsg(self, flag) -> str:
        """
        Prepares the Manual Focus message, and returns it as a string

        Params
        --
        flag: [int] 1: long shot in, 0, stop , -1: close shot

        Returns
        --
        [str] encoded msg if available. Otherwise, returns empty string
        """
        data=self.toHex(flag, 8)
        data_len = "0100"
        cmd_id = "06"
        return self.encodeMsg(data_len, data, cmd_id)

    def gimbalRotationMsg(self, yaw_speed, pitch_speed) -> str:
        """
        Prepares the Gimbal Rotation message, and returns it as a string

        Params
        --
        yaw_speed: [int] -100~0~100: Negative and positive represent two directions, higher or lower the number is away from 0, faster the rotation speed is. Send 0 when released from control command and gimbal stops rotation.
        pitch_speed: [int] -100~0~100: Negative and positive represent two directions, higher or lower the number is away from 0, faster the rotation speed is. Send 0 when released from control command and gimbal stops rotation.

        Returns
        --
        [str] encoded msg if available. Otherwise, returns empty string
        """
        data1=self.toHex(yaw_speed, 8)
        data2=self.toHex(pitch_speed, 8)
        data=data1+data2
        data_len = "0200"
        cmd_id = "07"
        return self.encodeMsg(data_len, data, cmd_id)

    def centerMsg(self) -> str:
        """
        Prepares the Center Rotation message, and returns it as a string

        Returns
        --
        [str] encoded msg if available. Otherwise, returns empty string
        """
        data="01"
        data_len = "0100"
        cmd_id = "08"
        return self.encodeMsg(data_len, data, cmd_id)

    def gimbalInfoMsg(self) -> str:
        """
        Prepares the Acquire Gimbal Configuration message, and returns it as a string

        Returns
        --
        [str] encoded msg if available. Otherwise, returns empty string
        """
        data=""
        data_len = "0000"
        cmd_id = "0a"
        return self.encodeMsg(data_len, data, cmd_id)

    def functionInfoMsg(self) -> str:
        """
        Prepares the Function Feedback Information message, and returns it as a string

        Returns
        --
        [str] encoded msg if available. Otherwise, returns empty string
        """
        data=""
        data_len = "0000"
        cmd_id = "0b"
        return self.encodeMsg(data_len, data, cmd_id)

    def takePhotoMsg(self) -> str:
        """
        Prepares the Take Photo message, and returns it as a string

        Returns
        --
        [str] encoded msg if available. Otherwise, returns empty string
        """
        data="00"
        data_len = "0100"
        cmd_id = "0c"
        return self.encodeMsg(data_len, data, cmd_id)

    def startStopRecordingMsg(self) -> str:
        """
        Prepares the Start/Stop Recording message, and returns it as a string

        Returns
        --
        [str] encoded msg if available. Otherwise, returns empty string
        """
        data="02"
        data_len = "0100"
        cmd_id = "0c"
        return self.encodeMsg(data_len, data, cmd_id)

    def lockModeMsg(self) -> str:
        """
        Prepares the Lock Mode message, and returns it as a string.

        Returns
        --
        [str] encoded msg if available. Otherwise, returns empty string
        """
        data="03"
        data_len = "0100"
        cmd_id = "0c"
        return self.encodeMsg(data_len, data, cmd_id)

    def followModeMsg(self) -> str:
        """
        Prepares the Follow Mode message, and returns it as a string.

        Returns
        --
        [str] encoded msg if available. Otherwise, returns empty string
        """
        data="04"
        data_len = "0100"
        cmd_id = "0c"
        return self.encodeMsg(data_len, data, cmd_id)

    def fpvModeMsg(self) -> str:
        """
        Prepares the FPV Mode message, and returns it as a string.

        Returns
        --
        [str] encoded msg if available. Otherwise, returns empty string
        """
        data="05"
        data_len = "0100"
        cmd_id = "0c"
        return self.encodeMsg(data_len, data, cmd_id)

    def gimbalAttitudeMsg(self) -> str:
        """
        Prepares the Gimbal Attitude message, and returns it as a string.

        Returns
        --
        [str] encoded msg if available. Otherwise, returns empty string
        """
        data=""
        data_len = "0000"
        cmd_id = "0d"
        return self.encodeMsg(data_len, data, cmd_id)
    
    def getFirmwareVersion(self):
        """
        Sends msg to request firmware version
        """
        msg = self.acquireFirmwareVersionMsg()
        print(msg)
        if len(msg)>0:
            self.sendMsg(msg)
            # Get feedback, timesout after 1 second
            server_msg = self.rcvMsg()
            if server_msg is not None:
                # TODO decode msg
                print("Server msg: ",server_msg)
                return server_msg
            else:
                print("[getFirmwareVersion] Did not get feedback from server")
                return None
        else:
            print("[getFirmwareVersion] Could not construct msg")

    def getGimbalAttitude(self):
        """
        Sends msg to request gimbal attitude
        """
        msg = self.gimbalAttitudeMsg()
        print(msg)
        if len(msg)>0:
            self.sendMsg(msg)
            # Get feedback
            server_msg = self.rcvMsg()
            if server_msg is not None:
                # TODO decode msg
                print("Server msg: ",server_msg)
                return server_msg
            else:
                print("[getGimbalAttitude] Did not get feedback from server")
                return None
        else:
            print("[getGimbalAttitude] Could not construct msg")

    def getHardwareID(self):
        """
        Sends msg to request hardware ID
        """
        msg = self.acquireHardwareIdMsg()
        print(msg)
        if len(msg)>0:
            self.sendMsg(msg)
            # Get feedback
            server_msg = self.rcvMsg()
            if server_msg is not None:
                # TODO decode msg
                print("Server msg: ",server_msg)
                return server_msg
            else:
                print("[getHardwareID] Did not get feedback from server")
                return None
        else:
            print("[getHardwareID] Could not construct msg")



def test():
    cam = ZR10SDK(server_ip="127.0.0.1", port=5005)

    cam.getGimbalAttitude()
    cam.getFirmwareVersion()
    cam.getHardwareID()

if __name__ == "__main__":
    test()