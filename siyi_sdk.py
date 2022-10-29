"""
Python implementation of ZR10 SDK by SIYI
ZR10 webpage: http://en.siyi.biz/en/Gimbal%20Camera/ZR10/overview/
Author : Mohamed Abdelkader
Email: mohamedashraf123@gmail.com
Copyright 2022

"""
import socket
from siyi_message import COMMAND, SIYIMESSAGE
from time import sleep, time
import logging
from utils import  toInt
import threading


class SIYISDK:
    def __init__(self, server_ip="192.168.144.25", port=37260, debug=False):
        """
        
        Params
        --
        - server_ip [str] IP address of the camera
        - port: [int] UDP port of the camera
        """
        self._debug= debug # print debug messages
        if self._debug:
            d_level = logging.DEBUG
        else:
            d_level = logging.INFO
        LOG_FORMAT=' [%(levelname)s] %(asctime)s [SIYISDK::%(funcName)s] :\t%(message)s'
        logging.basicConfig(format=LOG_FORMAT, level=d_level)
        self._logger = logging.getLogger(self.__class__.__name__)

        # Message sent to the camera
        self._out_msg = SIYIMESSAGE(debug=self._debug)
        
        # Message received from the camera
        self._in_msg = SIYIMESSAGE(debug=self._debug)        

        self._server_ip = server_ip
        self._port = port

        self._BUFF_SIZE=1024

        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._rcv_wait_t = 0.5 # Receiving wait time
        self._socket.settimeout(self._rcv_wait_t) # 1 second timeout for recvfrom()

        self._connected = False

        # Camera firmware version        
        self._fw_ver = ''

        # Hardware ID
        self._hw_id=''

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

        # Connection thread
        self._conn_loop_rate = 1 # seconds
        self._conn_thread = threading.Thread(target=self.connectionLoop, args=(self._conn_loop_rate,))
        self._stop = False # used to stop the above thread

        # Gimbal info thread @ 1Hz
        self._gimbal_info_loop_rate = 1
        self._g_info_thread = threading.Thread(target=self.gimbalInfoLoop,
                                                args=(self._gimbal_info_loop_rate,))

        # Gimbal attitude thread @ 10Hz
        self._gimbal_att_loop_rate = 0.1
        self._g_att_thread = threading.Thread(target=self.gimbalAttLoop,
                                                args=(self._gimbal_att_loop_rate,))

    def resetVars(self):
        """
        Resets variables to their initial values. For example, to prepare for a fresh connection
        """
        self._connected = False

        # Camera firmware version        
        self._fw_ver = ''

        # Hardware ID
        self._hw_id=''

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

        return True

    def connect(self, maxWaitTime=3.0):
        """
        Makes sure there is conenction with the camera before doing anything.
        It requests Frimware version for some time before it gives up

        Params
        --
        maxWaitTime [int] Maximum time to wait before giving up on connection
        """
        self._conn_thread.start()
        t0 = time()
        while(True):
            if self._connected:
                self._g_info_thread.start()
                self._g_att_thread.start()
                return True
            if (time() - t0)>maxWaitTime and not self._connected:
                self.disconnect()
                self._logger.error("Failed to connect to camera")
                return False

    def disconnect(self):
        self._stop = True # stop the connection checking thread
        self.resetVars()

        
    
    def checkConnection(self):
        """
        checks if there is live connection to the camera by requesting the Firmware version.
        This function is to be run in a thread at a defined frequency
        """
        val = self.getFirmwareVersion()
        if val is None:
            self._connected = False
        else:
            self._connected = True

    def connectionLoop(self, t):
        """
        This function is used in a thread to check connection status periodically

        Params
        --
        t [float] message frequency, secnod(s)
        """
        while(True):
            if self._stop:
                self._connected=False
                self.resetVars()
                self._logger.warning("Connection checking loop is stopped. Check your connection!")
                break
            val = self.checkConnection()
            sleep(t)

    def isConnected(self):
        return self._connected

    def gimbalInfoLoop(self, t):
        """
        This function is used in a thread to get gimbal info periodically

        Params
        --
        t [float] message frequency, secnod(s) 
        """
        while(True):
            if not self._connected:
                self._logger.warning("Stop gimbal info thread")
                break
            self.getGimbalInfo()
            sleep(t)

    def gimbalAttLoop(self, t):
        """
        This function is used in a thread to get gimbal attitude periodically

        Params
        --
        t [float] message frequency, secnod(s) 
        """
        while(True):
            if not self._connected:
                self._logger.warning("Stop gimbal attitude thread")
                break
            self.getGimbalAttitude()
            sleep(t)

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
            self._logger.warning("%s. Did not receive message within %s second(s)", e, self._rcv_wait_t)
        return data

    ###############################################################################
    #                                    Get  functions                           #
    ###############################################################################
    def getFirmwareVersion(self):
        """
        Returns Firmware version

        Returns
        --
        - [str] Currently returns firmware version as hexdecimal string.
             Returns None on failure
        """

        msg = self._out_msg.firmwareVerMsg()
        if len(msg)>0:
            good = self.sendMsg(msg)
            if not good:
                self._logger.error("Could not send message request. Check communication")
                return None

            # Get feedback, timesout after self._rcv_wait_t second
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

            self._fw_ver = data_str[8:16]
            self._logger.debug("Firmware version: %s", self._fw_ver)
            return self._fw_ver
                
        else:
            self._logger.error("Could not construct msg")
            return None

    def getHardwareID(self):
        """
        Returns Hardware ID

        Returns
        --
        - [string] Hardwre ID as string of hexadecimal. Returns None on failure
        """
        msg = self._out_msg.hwIdMsg()
        if len(msg)>0:
            good = self.sendMsg(msg)
            if not good:
                self._logger.error("Could not send message request. Check communication")
                return None

            # Get feedback, timesout after self._rcv_wait_t second(s)
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

            self._hw_id = data_str
            self._logger.debug("Hardware ID: %s", self._hw_id)
            return self._hw_id
                
        else:
            self._logger.error("Could not construct msg")
            return None

    def getGimbalAttitude(self):
        """
        Sends msg to request gimbal attitude, and returns attitude in degrees, and attitude speed in deg/s.
        Values are accurate to one decimal place.

        Returns
        --
        None on failure
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

            # Get feedback, timesout after self._rcv_wait_t second(s)
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

            self._yaw_deg = yaw_deg = toInt(data_str[2:4]+data_str[0:2]) /10.
            self._pitch_deg = pitch_deg = toInt(data_str[6:8]+data_str[4:6]) /10.
            self._roll_deg = roll_deg = toInt(data_str[10:12]+data_str[8:10]) /10.
            self._yaw_speed = yaw_velocity = toInt(data_str[14:16]+data_str[12:14]) /10.
            self._pitch_speed = pitch_velocity = toInt(data_str[18:20]+data_str[16:18]) /10.
            self._roll_speed = roll_velocity = toInt(data_str[22:24]+data_str[20:22]) /10.
            return yaw_deg, pitch_deg, roll_deg, yaw_velocity, pitch_velocity, roll_velocity
                
        else:
            self._logger.error("Could not construct msg")
            return None

    def getGimbalInfo(self):
        """
        Sends msg to request gimbal configuration information

        Returns
        --
        - None on failure
        - record_state: [int] Recording status 0:OFF, 1: ON, 2: TF card slot is empty, 3:(Recording) Data loss in TF card recorded video, please check TF card
        - mounting_dir: [int] Mounting direction 1: Normal, 2: Upside down
        """
        msg = self._out_msg.gimbalInfoMsg()
        if len(msg)>0:
            good = self.sendMsg(msg)
            if not good:
                self._logger.error("Could not send message request. Check communication")
                return None

            # Get feedback, timesout after self._rcv_wait_t second(s)
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
            self._recording_on = bool(record_state)
            # motion_mode = int(hex_str[8:10], base=16)
            mount_dir = int(data_str[-2:], base=16)
            self._mounting_dir = mount_dir
            return record_state, mount_dir
                
        else:
            self._logger.error("Could not construct msg")
            return None

    def getFuncFeedback(self):
        """
        Sends msg to request Function Feedback Information

        Returns
        --
        - None on failure
        - ack_data: [int]
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

            # Get feedback, timesout after self._rcv_wait_t second(s)
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

            # Get feedback, timesout after self._rcv_wait_t second(s)
            server_msg = self.rcvMsg()
            self._logger.debug("server_msg hex string: %s", server_msg.hex())

            if server_msg is None:
                self._logger.warning("Did not get feedback from camera")
                return False
            
            # Decode mesage            
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

    def setZoom(self, flag):
        """
        Sends zoom request

        Params
        --
        flag: [int] 1: start zoom in, 0: stop zoom, -1: start zoom out
        
        Returns
        --
        zoom_level: [int] 0~30. -1 if it fails
        """
        if (flag == 1):
            msg=self._out_msg.zoomInMsg()
        elif (flag == -1):
            msg=self._out_msg.zoomOutMsg()
        else:
            msg=self._out_msg.stopZoomMsg()

        if len(msg)>0:
            good = self.sendMsg(msg)
            if not good:
                self._logger.error("Could not send data. Check communication")
                return -1

            # Get feedback, timesout after self._rcv_wait_t second(s)
            server_msg = self.rcvMsg()
            self._logger.debug("server_msg hex string: %s", server_msg.hex())

            if server_msg is None:
                self._logger.warning("Did not get feedback from camera")
                return -1
            
            # Decode mesage            
            val = self._in_msg.decodeMsg(server_msg.hex())
            if val is None:
                return -1
            data_str, data_len, cmd_id = val[0], val[1], val[2]
            self._logger.debug("Data hex string: %s", data_str)

            self._zoom_level = int(data_str[2:4]+data_str[0:2], base=16) /10.
             
            return self._zoom_level
                
        else:
            self._logger.error("Could not construct msg")
            self._zoom_level=-1
            return self._zoom_level

    def setFocus(self, flag):
        """
        Sends manual focus request

        Params
        --
        flag: [int] 1: Long shot, 0: stop manual focus, -1: close shot
        
        Returns
        --
        True: Success
        False: Fail
        """
        if flag==1:
            msg = self._out_msg.longFocusMsg()
        elif flag==-1:
            msg = self._out_msg.closeFocusMsg()
        else:
            msg = self._out_msg.stopFocusMsg()
        if len(msg)>0:
            good = self.sendMsg(msg)
            if not good:
                self._logger.error("Could not send data. Check communication")
                return False

            # Get feedback, timesout after self._rcv_wait_t second(s)
            server_msg = self.rcvMsg()
            self._logger.debug("server_msg hex string: %s", server_msg.hex())

            if server_msg is None:
                self._logger.warning("Did not get feedback from camera")
                return False
            
            # Decode mesage            
            val = self._in_msg.decodeMsg(server_msg.hex())
            if val is None:
                return False
            data_str, data_len, cmd_id = val[0], val[1], val[2]
            self._logger.debug("Data hex string: %s", data_str)

            ret = int(data_str, base=16)
            
            return bool(ret)
                
        else:
            self._logger.error("Could not construct msg")
            return False

    def centerGimbal(self):
        """
        Sends msg to set gimbal at the center position

        Returns
        --
        [bool] True if successful. False otherwise
        """
        msg = self._out_msg.centerMsg()
        if len(msg)>0:
            good = self.sendMsg(msg)
            if not good:
                self._logger.error("Could not send data. Check communication")
                return False

            # Get feedback, timesout after self._rcv_wait_t second(s)
            server_msg = self.rcvMsg()

            if server_msg is None:
                self._logger.warning("Did not get feedback from camera")
                return False

            self._logger.debug("server_msg hex string: %s", server_msg.hex())
            
            # Decode mesage            
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

    def setGimbalSpeed(self, yaw_speed, pitch_speed):
        """
        Sends msg to set gimbal yaw and pitch speeds

        Params
        --
        yaw_speed: [int] -100~0~100. Percentage of max speed
        pitch_speed: [int] same as  yaw_speed

        Returns
        --
        [bool] True if successful. False otherwise
        """
        msg = self._out_msg.gimbalSpeedMsg(yaw_speed, pitch_speed)
        if len(msg)>0:
            good = self.sendMsg(msg)
            if not good:
                self._logger.error("Could not send data. Check communication")
                return False

            # Get feedback, timesout after self._rcv_wait_t second(s)
            server_msg = self.rcvMsg()
            self._logger.debug("server_msg hex string: %s", server_msg.hex())

            if server_msg is None:
                self._logger.warning("Did not get feedback from camera")
                return False
            
            # Decode mesage            
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

    def setGimbalRotation(self, yaw, pitch, err_thresh=0.5, kp=4):
        """
        Sets gimbal attitude angles yaw and pitch in degrees

        Params
        --
        yaw: [float] desired yaw in degrees
        pitch: [float] desired pitch in degrees
        err_thresh: [float] acceptable error threshold, in degrees, to stop correction
        kp [float] proportional gain
        """
        if (pitch >25 or pitch <-90):
            self._logger.error("desired pitch is outside controllable range -90~25")
            return

        if (yaw >45 or yaw <-45):
            self._logger.error("Desired yaw is outside controllable range -45~45")
            return

        th = err_thresh
        gain = kp
        while(True):
            vals = self.getGimbalAttitude()
            if vals is None:
                self._logger.warning("Gimbal attitude feedback is None. Not setting rotations")
                break

            y,p,r, y_s, p_s, r_s = vals[0], vals[1], vals[2], vals[3], vals[4], vals[5]
            yaw_err = -yaw + y # NOTE for some reason it's reversed!!
            pitch_err = pitch - p

            self._logger.debug("yaw_err= %s", yaw_err)
            self._logger.debug("pitch_err= %s", pitch_err)

            if (abs(yaw_err) <= th and abs(pitch_err)<=th):
                ret = self.setGimbalSpeed(0, 0)
                self._logger.info("Goal rotation is reached")
                break

            y_speed_sp = max(min(100, int(gain*yaw_err)), -100)
            p_speed_sp = max(min(100, int(gain*pitch_err)), -100)
            self._logger.debug("yaw speed setpoint= %s", y_speed_sp)
            self._logger.debug("pitch speed setpoint= %s", p_speed_sp)
            ret = self.setGimbalSpeed(y_speed_sp, p_speed_sp)
            if(not ret):
                self._logger.warning("Could not set gimbal speed")
                break

            sleep(0.1) # command frequency

    def takePhoto(self):
        """
        Sends a message to take a single photo

        Returns
        --
        True: if success. False otherwise
        """
        msg = self._out_msg.takePhotoMsg()
        if len(msg)>0:
            good = self.sendMsg(msg)
            if not good:
                self._logger.error("Could not send data. Check communication")
                return False

        # NOTE ack is not yet implemented for photo
        ack_code = self.getFuncFeedback()

        if ack_code is None:
            self._logger.warning("Could not get acknowledgement")
            return False

        if ack_code==0:
            return True
        else:
            self._logger.error("Could not take photo. Error code: %s", ack_code)
            return False

    def toggleRecording(self):
        """
        Sends a message to toggle recording state. 
        
        Returns
        --
        [int] 1: Record is ON. Record is OFF. 2: TF card slot is empty. 3: Data loss, check SD card
        """
        msg = self._out_msg.recordMsg()
        if len(msg)>0:
            self.sendMsg(msg)
            good = self.sendMsg(msg)
            if not good:
                self._logger.error("Could not send data. Check communication")
                return False

        ack_code = self.getFuncFeedback()
        if ack_code is None:
            self._logger.warning("Could not get acknowledgement")

        if ack_code==4:
            self._logger.error("Fail to record a video. Please check if TF card is inserted" )
            return False

        info=self.getGimbalInfo()
        if info is None:
            self._logger.warning("Could not get gimbal info for acknowledgement to check recording state")
            return False

        record_state= info[0]
        
        if record_state == 1:
            self._logger.info("Recording is ON")
            self._recording_on = True
        elif record_state == 0:
            self._logger.info("Recording is OFF")
            self._recording_on = False
        else:
            self._logger.warning("Record state is unknown . Code: %s", record_state)

        return record_state

    def setFPVMode(self):
        """
        Sets FPV mode

        Returns
        --
        True: if success. False otherwise
        """
        msg = self._out_msg.fpvModeMsg()
        if len(msg)>0:
            self.sendMsg(msg)
            good = self.sendMsg(msg)
            if not good:
                self._logger.error("Could not send data. Check communication")
                return False

        ack_code = self.getFuncFeedback()
        if ack_code is None:
            self._logger.warning("Could not get acknowledgement")

        if ack_code==0:
            self._logger.info("Mode setting is successful" )
            return True
        else:
            self._logger.warning("Could not set mode")
            return False

    def setFollowMode(self):
        """
        Sets FPV mode

        Returns
        --
        True: if success. False otherwise
        """
        msg = self._out_msg.followModeMsg()
        if len(msg)>0:
            self.sendMsg(msg)
            good = self.sendMsg(msg)
            if not good:
                self._logger.error("Could not send data. Check communication")
                return False

        ack_code = self.getFuncFeedback()
        if ack_code is None:
            self._logger.warning("Could not get acknowledgement")

        if ack_code==0:
            self._logger.info("Mode setting is successful" )
            return True
        else:
            self._logger.warning("Could not set mode")
            return False

    def setLockMode(self):
        """
        Sets Lock mode

        Returns
        --
        True: if success. False otherwise
        """
        msg = self._out_msg.lockModeMsg()
        if len(msg)>0:
            self.sendMsg(msg)
            good = self.sendMsg(msg)
            if not good:
                self._logger.error("Could not send data. Check communication")
                return False

        ack_code = self.getFuncFeedback()
        if ack_code is None:
            self._logger.warning("Could not get acknowledgement")

        if ack_code==0:
            self._logger.info("Mode setting is successful" )
            return True
        else:
            self._logger.warning("Could not set mode")
            return False

        

if __name__ == "__main__":
    cam = SIYISDK(debug=True)

    val = cam.connect()
    print("Connection : ", val)

    # cam._rcv_wait_t = 1.0

    # fw = cam.getFirmwareVersion()
    # print("Firmware version: ", fw)
    # hw = cam.getHardwareID()
    # print("Hardware ID: ", hw)
    # val = cam.getGimbalAttitude()
    # if val is not None:
    #     print("Yaw deg: ", val[0])
    #     print("pitch deg: ", val[1])
    #     print("Roll deg: ", val[2])
    #     print("Yaw speed: ", val[3])
    #     print("Pitch speed: ", val[4])
    #     print("Roll speed: ", val[5])

    # val = cam.getGimbalInfo()
    # if val is not None:
    #     print("Recording state: ", val[0])
    #     print("Mounting Direction: ", val[1])

    # val = cam.setAutoFocus()
    # print("Auto focus: ", val)

    # val = cam.setZoom(1)
    # print("Zoom in: ", val)
    # sleep(2)
    # val = cam.setZoom(0)
    # print("Stop zoom: ", val)
    # sleep(2)
    # val = cam.setZoom(-1)
    # print("Zoom out: ", val)
    # sleep(2)
    # val = cam.setZoom(0)
    # print("Stop zoom: ", val)

    # val = cam.setFocus(1)
    # print("Manual focus, long: ", val)
    # sleep(1)
    # val = cam.setFocus(0)
    # print("Manual focus, stop: ", val)
    # sleep(1)
    # val = cam.setFocus(-1)
    # print("Manual focus, close: ", val)
    # sleep(1)
    # cam.setFocus(0)

    # val = cam.setGimbalSpeed(10,10)
    # sleep(1)
    # val = cam.setGimbalSpeed(0,0)
    # sleep(0.1)
    # val = cam.centerGimbal()
    # print("Center gimbal: ",val )

    # cam.setGimbalRotation(45,-80, err_thresh=0.5, kp=4)
    # val = cam.getGimbalAttitude()
    # if val is not None:
    #     yaw = val[0]
    #     pitch = val[1]

    #     print("Current yaw= ", yaw)
    #     print("Current pitch= ", pitch)

    # val = cam.takePhoto()
    # print("Taking photo... : ", val)

    # val = cam.toggleRecording()
    # print(" Recording ON? ", cam._recording_on)