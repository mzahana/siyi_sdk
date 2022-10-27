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
from time import sleep
import crc16
import logging

LOG_FORMAT='%(asctime)s [ZR10SDK] [%(levelname)s] [%(funcName)s]:\t%(message)s'


class COMMAND(Enum):
    ACQUIRE_FW_VER = '01'
    ACQUIRE_HW_ID = '02'
    AUTO_FOCUS = '04'
    MANUAL_ZOOM = '05'
    MANUAL_FOCUS = '06'
    GIMBAL_ROT = '07'
    CENTER = '08'
    ACQUIRE_GIMBAL_INFO = '0A'
    FUNC_FEEDBACK_INFO = '0B'
    PHOTO_VIDEO_HDR = '0C'
    ACQUIRE_GIMBAL_ATT = '0D'

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
        # Sequence, 2 bytes. Should be incremented on each msg send
        # NOTE Low byte on the left!
        self._seq= '0000'

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
        L = len(data)

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
        [str] string of hexadecimal of data bytes.
        """
        data = ""
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
        msg = "556601000000000164c4"
        return msg
    
    def hwIdMsg(self):
        """
        Returns message string for the Acquire Hardware ID
        """
        msg="556601000000000207f4"

    def gimbalInfoMsg(self):
        """
        Gimbal status information msg
        """
        msg="556601000000000a0f75"
        return msg

    def takePhotoMsg(self):
        """
        Take photo msg
        """
        msg="556601010000000c0034ce"
        return msg

    def recordMsg(self):
        """
        Video Record msg
        """
        msg="556601010000000c0276ee"
        return msg

    def autoFocusMsg(self):
        """
        Auto focus msg
        """
        msg="556601010000000401bc57"
        return msg

    def centerMsg(self):
        """
        Center gimbal msg
        """
        msg="556601010000000801d112"
        return msg

    def lockModeMsg(self):
        """
        Lock mode msg
        """
        msg="556601010000000c0357fe"

    def zoomInMsg(self):
        """
        Zoom in Msg
        """
        msg= "5566010100000005018d64"
        return msg

    def zoomOutMsg(self):
        """
        Zoom out Msg
        """
        msg= "5566010100000005FF5c6a"
        return msg

    def stopZoomMsg(self):
        """
        Stop Zoom Msg
        """
        msg= "5566010100000005FF5c6a"
        return msg


    


class SIYISDK:
    def __init__(self) -> None:
        pass