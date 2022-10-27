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
from enum import Enum
import socket
from time import CLOCK_THREAD_CPUTIME_ID, sleep
import crc16
import logging
from utils import toHex, toInt

LOG_FORMAT='%(asctime)s [SIYISDK] [%(levelname)s] [%(funcName)s]:\t%(message)s'


class COMMAND:
    ACQUIRE_FW_VER = '01'
    ACQUIRE_HW_ID = '02'
    AUTO_FOCUS = '04'
    MANUAL_ZOOM = '05'
    MANUAL_FOCUS = '06'
    GIMBAL_ROT = '07'
    CENTER = '08'
    ACQUIRE_GIMBAL_INFO = '0a'
    FUNC_FEEDBACK_INFO = '0b'
    PHOTO_VIDEO_HDR = '0c'
    ACQUIRE_GIMBAL_ATT = '0d'

class SIYIMESSAGE:
    """
    Structure of SIYI camera messages
    """
    def __init__(self) -> None:
        self._debug= False # print debug messages
        if self._debug:
            d_level = logging.DEBUG
        else:
            d_level = logging.INFO
        logging.basicConfig(format=LOG_FORMAT, level=d_level)
        self._logger = logging.getLogger(__name__)

        self.HEADER='5566'# STX, 2 bytes
        self._ctr ='01'        

        self._seq= 0

        self._cmd_id='00' # 1 byte
        
        self._data_len = 0
        
        # String of data byes (in hex)
        self._data=''

        self._crc16='0000' # low byte (2 characters) on the left!

    def calcCRC16(self, msg: str):
        """
        Calculates the two bytes CRC16, with swaped order, and returns them as a string
        Returns empty sting if there is an error
        """

        crc = ""
        if not isinstance(msg, str):
            self._logger.error("Message is not string")
            return crc
        try:
            b = bytes.fromhex(msg)
            int_crc = crc16.crc16xmodem(b)
            str_crc = format(int_crc, 'x')
            # Make sure we get 4 characters
            if len(str_crc)==3 or len(str_crc)==1:
                # Make it even number of characters
                str_crc = "0"+str_crc
            # Reverse bytes, according to SIYI SDK
            c1 = str_crc[2:] # low byte
            c2 = str_crc[0:2] # high byte
            # low+high
            crc = c1+c2
            return crc
        except Exception as e:
            self._logger.error("%s", e)
            return crc

    def incrementSEQ(self, val):
        """
        Increments sequence number by one, converts them to hex, and revereses the byte order.

        Params
        --
        - val [int] Integer value , max is 65535

        Returns
        --
        seq_str: [string] String value of the sequence number in reveresed byte order
        """
        
        if not isinstance(val, int):
            self._logger.warning("Sequence value is not integer. Returning zero")
            return "0000"
        if val> 65535:
            self._logger.warning("Sequence value is greater than 65535. Resetting to zero")
            return "0000"
        if val<0:
            self._logger.warning("Sequence value is negative. Resetting to zero")
            return "0000"

        seq = val+1
        seq_hex = hex(seq)
        seq_hex = seq_hex[2:] # remove '0x'
        if len(seq_hex)==3 or len(seq_hex)==1:
            seq_hex = '0'+seq_hex

        # We nede to make sure we have 2 bytes (4 characters)
        if len(seq_hex)==2:
            seq_str = seq_hex+'00'
        else:
            low_b = seq_hex[-2:]
            high_b = seq_hex[0:2]
            seq_str = low_b+high_b

        return seq_str

    def computeDataLen(self, data):
        """
        Computes the data lenght (number of bytes) of data, and return a string of two bytes in reveresed order

        Params
        --
        data [string] string of dataa bytes in hex

        Returns
        --
        [string] String of two bytes (for characters), in reversed order
        """

        if not isinstance(data, str):
            self._logger.error("Data is not opf type string")
            return "0000"
        # We expect number of chartacters to be even (each byte is represented by two cahrs e.g. '0A')
        if (len(data)%2) != 0:
            data = '0'+data # Pad 0 from the left, as sometimes it's ignored!
        L = int(len(data)/2)

        len_hex = hex(L)
        len_hex = len_hex[2:] # remove '0x'
        if len(len_hex)==3 or len(len_hex)==1:
            len_hex = '0'+len_hex

        # We need to make sure we have 2 bytes (4 characters)
        if len(len_hex)==2:
            len_str = len_hex+'00'
        else:
            low_b = len_hex[-2:]
            high_b = len_hex[0:2]
            len_str = low_b+high_b

        return len_str

    def decodeMsg(self, msg):
        """
        Decodes messages string, and returns the DATA bytes.

        Params
        --
        msg: [str] full message stinf in hex

        Returns
        --
        - data [str] string of hexadecimal of data bytes.
        - data_len [int] Number of data bytes
        - cmd_id [str] command ID
        """
        data = None
        if not isinstance(msg, str):
            self._logger.error("Input message is not a string")
            return data

        if len(msg)==0:
            self._logger.error("No data to decode")
            return data

        # check crc16, if msg is OK!
        msg_crc=msg[-4:] # last 4 characters
        payload=msg[:-4]
        expected_crc=self.calcCRC16(payload)
        if expected_crc!=msg_crc:
            self._logger.error("CRC16 is not valid. Message might be corrupted!")
            return data
        
        # Data length, bytes are reversed, according to SIYI SDK
        high_b = msg[6:8] # high byte
        low_b = msg[8:10] # low byte
        data_len = low_b+high_b
        data_len = int('0x'+data_len, base=16)
        char_len = data_len*2 # number of characters. Each byte is represented by two characters in hex, e.g. '0A'= 2 chars
        
        cmd_id = msg[14:16]
        
        data = msg[16:16+char_len]
        
        self._data = data
        self._data_len = data_len
        self._cmd_id = cmd_id

        return data, data_len, cmd_id

    def encodeMsg(self, data, cmd_id):
        """
        Encodes a msg according to SDK protocol

        Returns
        --
        [str] Encoded msg. Empty string if crc16 is not successful
        """
        seq = self.incrementSEQ(self._seq)
        data_len = self.computeDataLen(data)
        msg_front = self.HEADER+self._ctr+data_len+seq+cmd_id+data
        crc = self.calcCRC16(msg_front)
        if crc is not None:
            msg = msg_front+crc
            self._logger.debug("Encoded msg: %s", msg)
            return msg
        else:
            self._logger.error("Could not encode message. crc16 is None")
            return ''

    def firmwareVerMsg(self):
        """
        Returns message string of the Acuire Firmware Version msg
        """
        data=""
        cmd_id = COMMAND.ACQUIRE_FW_VER
        return self.encodeMsg(data, cmd_id)
    
    def hwIdMsg(self):
        """
        Returns message string for the Acquire Hardware ID
        """
        data=""
        cmd_id = COMMAND.ACQUIRE_HW_ID
        return self.encodeMsg(data, cmd_id)

    def gimbalInfoMsg(self):
        """
        Gimbal status information msg
        """
        data=""
        cmd_id = COMMAND.ACQUIRE_GIMBAL_INFO
        return self.encodeMsg(data, cmd_id)

    def funcFeedbackMsg(self):
        """
        Function feedback information msg
        """
        data=""
        cmd_id = COMMAND.FUNC_FEEDBACK_INFO
        return self.encodeMsg(data, cmd_id)

    def takePhotoMsg(self):
        """
        Take photo msg
        """
        data="00"
        cmd_id = COMMAND.PHOTO_VIDEO_HDR
        return self.encodeMsg(data, cmd_id)

    def recordMsg(self):
        """
        Video Record msg
        """
        data="02"
        cmd_id = COMMAND.PHOTO_VIDEO_HDR
        return self.encodeMsg(data, cmd_id)

    def autoFocusMsg(self):
        """
        Auto focus msg
        """
        data="01"
        cmd_id = COMMAND.AUTO_FOCUS
        return self.encodeMsg(data, cmd_id)

    def centerMsg(self):
        """
        Center gimbal msg
        """
        data="01"
        cmd_id = COMMAND.CENTER
        return self.encodeMsg(data, cmd_id)

    def lockModeMsg(self):
        """
        Lock mode msg
        """
        data="03"
        cmd_id = COMMAND.PHOTO_VIDEO_HDR
        return self.encodeMsg(data, cmd_id)

    def followModeMsg(self):
        """
        Follow mode msg
        """
        data="04"
        cmd_id = COMMAND.PHOTO_VIDEO_HDR
        return self.encodeMsg(data, cmd_id)
    
    def fpvModeMsg(self):
        """
        FPV mode msg
        """
        data="05"
        cmd_id = COMMAND.PHOTO_VIDEO_HDR
        return self.encodeMsg(data, cmd_id)

    def gimbalAttMsg(self):
        """
        Acquire Gimbal Attiude msg
        """
        data=""
        cmd_id = COMMAND.ACQUIRE_GIMBAL_ATT
        return self.encodeMsg(data, cmd_id)

    def zoomInMsg(self):
        """
        Zoom in Msg
        """
        data="01"
        cmd_id = COMMAND.MANUAL_ZOOM
        return self.encodeMsg(data, cmd_id)

    def zoomOutMsg(self):
        """
        Zoom out Msg
        """
        data="ff"
        cmd_id = COMMAND.MANUAL_ZOOM
        return self.encodeMsg(data, cmd_id)

    def stopZoomMsg(self):
        """
        Stop Zoom Msg
        """
        data="00"
        cmd_id = COMMAND.MANUAL_ZOOM
        return self.encodeMsg(data, cmd_id)

    def longFocusMsg(self):
        """
        Focus 1 Msg
        """
        data="01"
        cmd_id = COMMAND.MANUAL_FOCUS
        return self.encodeMsg(data, cmd_id)

    def closeFocusMsg(self):
        """
        Focus -1 Msg
        """
        data="ff"
        cmd_id = COMMAND.MANUAL_FOCUS
        return self.encodeMsg(data, cmd_id)

    def stopFocusMsg(self):
        """
        Focus 0 Msg
        """
        data="00"
        cmd_id = COMMAND.MANUAL_FOCUS
        return self.encodeMsg(data, cmd_id)

    def gimbalSpeedMsg(self, yaw_speed, pitch_speed):
        """
        Gimbal rotation Msg.
        Values -100~0~100: Negative and positive represent two directions,
        higher or lower the number is away from 0, faster the rotation speed is.
        Send 0 when released from control command and gimbal stops rotation.

        Params
        --
        - yaw_speed [int] in degrees
        - pitch_speed [int] in degrees
        """
        data1=self.toHex(yaw_speed, 8)
        data2=self.toHex(pitch_speed, 8)
        data=data1+data2
        cmd_id = COMMAND.GIMBAL_ROT
        return self.encodeMsg(data, cmd_id)

    


class SIYISDK:
    def __init__(self, server_ip="192.168.144.25", port=37260):
        """"
        Params
        --
        server_ip [str] IP address of the camera
        port: [int] UDP port of the camera
        """
        self._debug= True # print debug messages
        if self._debug:
            d_level = logging.DEBUG
        else:
            d_level = logging.INFO
        logging.basicConfig(format=LOG_FORMAT, level=d_level)
        self._logger = logging.getLogger(__name__)

        # Message to be sent to the camera
        self._out_msg = SIYIMESSAGE()
        self._out_msg._debug = self._debug
        
        # Message received from the camera
        self._in_msg = SIYIMESSAGE()
        self._in_msg._debug = self._debug
        

        self._server_ip = server_ip
        self._port = port

        self._BUFF_SIZE=1024

        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._rcv_wait_t = 1.0 # Receiving wait time
        self._socket.settimeout(self._rcv_wait_t) # 1 second timeout for recvfrom()

        self._connected = False

        # Current hybrid Zoom level 1~30
        self._zoom_level=1.0

        # Current gimbal attitude
        self._yaw_deg = 0.0
        self._pitch_deg = 0.0
        self._roll_deg = 0.0
        self._yaw_speed = 0.0
        self._pitch_speed = 0.0
        self._roll_speed = 0.0

        self._hdr_on = False

        self._recording_on = False

        # 1: Normal. 2: Upside down
        self._mounting_dir = 1

        # 0: Lock, 1: Follow, 2: FPV
        self._motion_mode = 1

    def connection(self):
        """
        checks if there is live connection to the camera
        """
        pass

    def sendMsg(self, msg):
        """
        Sends a message to the camera

        Params
        --
        msg [str] Message to send
        """
        b = bytes.fromhex(msg)
        try:
            self._socket.sendto(b, (self._server_ip, self._port))
            return True
        except Exception as e:
            self._logger.error("Could not send bytes")
            return False

    def rcvMsg(self):
        data=None
        try:
            data,addr = self._socket.recvfrom(self._BUFF_SIZE)
        except Exception as e:
            self._logger.error("%s. Did not receive message within %s second(s)", e, self._rcv_wait_t)
        return data

    ###############################################################################
    #                                    Get  functions                           #
    ###############################################################################
    def getFirmwareVersion(self):
        """
        Returns Firmware version

        Returns
        --
        - [str] Currently returns firmware version as hexdecimal string
        """

        msg = self._out_msg.firmwareVerMsg()
        if len(msg)>0:
            good = self.sendMsg(msg)
            if not good:
                self._logger.error("Could not send message request. Check communication")
                return None

            # Get feedback, timesout after 1 second
            server_msg = self.rcvMsg()
            if server_msg is None:
                self._logger.warning("Did not get feedback from camera")
                return None

            # decode msg
            val = self._in_msg.decodeMsg(server_msg.hex())
            if val is None:
                return None
            data_str, data_len, cmd_id = val[0], val[1], val[2]
            if cmd_id != COMMAND.ACQUIRE_FW_VER:
                self._logger.error("Command ID did not match")
                return None
            
            self._logger.debug("Data hex string: %s", data_str)
            if len(data_str)==0:
                self._logger.error("Decoded msg is empty")
                return None

            firmware_ver = data_str[8:16]
            self._logger.debug("Firmware version: %s", firmware_ver)
            return firmware_ver
                
        else:
            self._logger.error("Could not construct msg")
            return None

    def getHardwareID(self):
        """
        Returns Hardware ID

        Returns
        --
        - [string] Hardwre ID as string of hexadecimal
        """
        msg = self._out_msg.hwIdMsg()
        if len(msg)>0:
            good = self.sendMsg(msg)
            if not good:
                self._logger.error("Could not send message request. Check communication")
                return None

            # Get feedback, timesout after 1 second
            server_msg = self.rcvMsg()
            if server_msg is None:
                self._logger.warning("Did not get feedback from camera")
                return None

            # decode msg
            val = self._in_msg.decodeMsg(server_msg.hex())
            if val is None:
                return None
            data_str, data_len, cmd_id = val[0], val[1], val[2]
            if cmd_id != COMMAND.ACQUIRE_HW_ID:
                self._logger.error("Command ID did not match")
                return None
            
            self._logger.debug("Data hex string: %s", data_str)
            if len(data_str)==0:
                self._logger.error("Decoded msg is empty")
                return None

            hw_id = data_str
            self._logger.debug("Hardware ID: %s", hw_id)
            return hw_id
                
        else:
            self._logger.error("Could not construct msg")
            return None

    def getGimbalAttitude(self):
        """
        Sends msg to request gimbal attitude, and returns attitude in degrees, and attitude speed in deg/s.
        Values are accurate to one decimal place.

        Returns
        --
        yaw_deg: [float] yaw in degrees
        pitch_deg: [float] pitch in degrees
        roll_deg: [float] roll in degrees
        yaw_velocity: [float] yaw speed in degrees/second
        pitch_velocity: [float] pitch speed in degrees/second
        roll_velocity: [float] roll speed in degrees/second
        """
        msg = self._out_msg.gimbalAttMsg()
        if len(msg)>0:
            good = self.sendMsg(msg)
            if not good:
                self._logger.error("Could not send message request. Check communication")
                return None

            # Get feedback, timesout after 1 second
            server_msg = self.rcvMsg()
            if server_msg is None:
                self._logger.warning("Did not get feedback from camera")
                return None

            self._logger.debug("Server message: %s", server_msg.hex())

            # decode msg
            val = self._in_msg.decodeMsg(server_msg.hex())
            if val is None:
                return val
            data_str, data_len, cmd_id = val[0], val[1], val[2]
            if cmd_id != COMMAND.ACQUIRE_GIMBAL_ATT:
                self._logger.error("Command ID did not match")
                return None
            
            self._logger.debug("Data hex string: %s", data_str)
            if len(data_str)==0:
                self._logger.error("Decoded msg is empty")
                return None

            yaw_deg = toInt(data_str[2:4]+data_str[0:2]) /10.
            pitch_deg = toInt(data_str[6:8]+data_str[4:6]) /10.
            roll_deg = toInt(data_str[10:12]+data_str[8:10]) /10.
            yaw_velocity = toInt(data_str[14:16]+data_str[12:14]) /10.
            pitch_velocity = toInt(data_str[18:20]+data_str[16:18]) /10.
            roll_velocity = toInt(data_str[22:24]+data_str[20:22]) /10.
            return yaw_deg, pitch_deg, roll_deg, yaw_velocity, pitch_velocity, roll_velocity
                
        else:
            self._logger.error("Could not construct msg")
            return None

    def getGimbalInfo(self):
        """
        Sends msg to request gimbal configuration information

        Returns
        --
        - record_state: [int] Recording status 0:OFF, 1: ON, 2: TF card slot is empty, 3:(Recording) Data loss in TF card recorded video, please check TF card
        - mounting_dir: [int] Mounting direction 1: Normal, 2: Upside down
        """
        msg = self._out_msg.gimbalInfoMsg()
        if len(msg)>0:
            good = self.sendMsg(msg)
            if not good:
                self._logger.error("Could not send message request. Check communication")
                return None

            # Get feedback, timesout after 1 second
            server_msg = self.rcvMsg()
            if server_msg is None:
                self._logger.warning("Did not get feedback from camera")
                return None

            self._logger.debug("Server message: %s", server_msg.hex())

            # decode msg
            val = self._in_msg.decodeMsg(server_msg.hex())
            if val is None:
                return None
            data_str, data_len, cmd_id = val[0], val[1], val[2]
            self._logger.debug("Data Length: %s", data_len)
            if cmd_id != COMMAND.ACQUIRE_GIMBAL_INFO:
                self._logger.error("Command ID did not match")
                return None
            
            self._logger.debug("Data hex string: %s", data_str)
            if len(data_str)==0:
                self._logger.error("Decoded msg is empty")
                return None

            # hdr_state = int(hex_str[2:4], base=16)
            record_state = int(data_str[-4:-2], base=16)
            # motion_mode = int(hex_str[8:10], base=16)
            mount_dir = int(data_str[-2:], base=16)
            return record_state, mount_dir
                
        else:
            self._logger.error("Could not construct msg")
            return None

    def getFuncFeedback(self):
        """
        Sends msg to request Function Feedback Information

        Returns
        --
        ack_data: [int]
                    0: success, 1: Fail to take a photo (Please check if TF card is inserted)
                    2: HDR ON, 3: HDR OFF
                    4: Fail to record a video (Please check if TF card is inserted)
        """
        msg = self._out_msg.funcFeedbackMsg()
        if len(msg)>0:
            good = self.sendMsg(msg)
            if not good:
                self._logger.error("Could not send message request. Check communication")
                return None

            # Get feedback, timesout after 1 second
            server_msg = self.rcvMsg()
            if server_msg is None:
                self._logger.warning("Did not get feedback from camera")
                return None

            self._logger.debug("Server message: %s", server_msg.hex())

            # decode msg
            val = self._in_msg.decodeMsg(server_msg.hex())
            if val is None:
                return None
            data_str, data_len, cmd_id = val[0], val[1], val[2]
            self._logger.debug("Data Length: %s", data_len)
            if cmd_id != COMMAND.FUNC_FEEDBACK_INFO:
                self._logger.error("Command ID did not match")
                return None
            
            self._logger.debug("Data hex string: %s", data_str)
            if len(data_str)==0:
                self._logger.error("Decoded msg is empty")
                return None

            ack_data = int(data_str, base=16)
            return ack_data
                
        else:
            self._logger.error("Could not construct msg")
            return None

    ###############################################################################
    #                                    Set  functions                           #
    ###############################################################################
    def setAutoFocus(self):
        """
        Sends msg to request auto focus.

        Reutrns
        --
        True: Success
        False: Fail
        """
        msg = self._out_msg.autoFocusMsg()
        self._logger.debug("autofocus hex string: %s", msg)
        
        if len(msg)>0:
            good = self.sendMsg(msg)
            if not good:
                self._logger.error("Could not send data. Check communication")
                return False

            # Get feedback, timesout after 1 second
            server_msg = self.rcvMsg()
            self._logger.debug("server_msg hex string: %s", server_msg.hex())

            if server_msg is None:
                self._logger.warning("Did not get feedback from camera")
                return False
            
            # Decode mesage
            data_s = self._in_msg.decodeMsg(server_msg.hex())
            
            val = self._in_msg.decodeMsg(server_msg.hex())
            if val is None:
                return False
            data_str, data_len, cmd_id = val[0], val[1], val[2]
            self._logger.debug("Data hex string: %s", data_str)

            flag = int(data_str, base=16)
            if flag==1:
                return True
            else:
                return False
                
        else:
            self._logger.error("Could not construct msg")
            return False

    

if __name__ == "__main__":
    cam = SIYISDK()

    fw = cam.getFirmwareVersion()
    print("Firmware version: ", fw)
    hw = cam.getHardwareID()
    print("Hardware ID: ", hw)
    val = cam.getGimbalAttitude()
    if val is not None:
        print("Yaw deg: ", val[0])
        print("pitch deg: ", val[1])
        print("Roll deg: ", val[2])
        print("Yaw speed: ", val[3])
        print("Pitch speed: ", val[4])
        print("Roll speed: ", val[5])

    val = cam.getGimbalInfo()
    if val is not None:
        print("Recording state: ", val[0])
        print("Mounting Direction: ", val[1])