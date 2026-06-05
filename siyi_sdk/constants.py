# Copyright (c) 2026 Mohamed Abdelkader <mohamedashraf123@gmail.com>
# All rights reserved.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

"""Protocol constants for the SIYI SDK.

This module contains all protocol-level constants including:
- Frame structure constants (STX, CTRL flags, header lengths)
- Command IDs from the SIYI SDK protocol specification
- CRC-16/XMODEM polynomial and lookup table
- Default network endpoints and hardware IDs
- Laser ranging constants
"""

from __future__ import annotations

from typing import Final

# =============================================================================
# Frame Structure Constants
# =============================================================================

# Start marker (little-endian on wire: 0x55 0x66)
STX: Final[int] = 0x6655
STX_BYTES: Final[bytes] = b"\x55\x66"

# Control byte flags (bit-field: bit[0]=need_ack, bit[1]=ack_pack)
CTRL_NEED_ACK: Final[int] = 0x01  # bit[0]: sender needs receiver to respond
CTRL_ACK_PACK: Final[int] = 0x02  # bit[1]: this frame IS a response/ACK

# Frame layout sizes
HEADER_LEN: Final[int] = 8  # STX(2) + CTRL(1) + Data_len(2) + SEQ(2) + CMD_ID(1)
CRC_LEN: Final[int] = 2
MIN_FRAME_LEN: Final[int] = 10  # HEADER_LEN + CRC_LEN (empty payload)

# Sequence number maximum
SEQ_MAX: Final[int] = 0xFFFF

# Integer bounds
UINT64_MAX: Final[int] = 0xFFFFFFFFFFFFFFFF

# =============================================================================
# CRC-16/XMODEM Constants
# =============================================================================

CRC16_POLY: Final[int] = 0x1021  # X^16 + X^12 + X^5 + 1
CRC16_INIT: Final[int] = 0x0000  # Initial CRC value

# CRC16 lookup table from SIYI SDK Protocol Chapter 4 (verbatim)
CRC16_TABLE: Final[tuple[int, ...]] = (
    0x0000,
    0x1021,
    0x2042,
    0x3063,
    0x4084,
    0x50A5,
    0x60C6,
    0x70E7,
    0x8108,
    0x9129,
    0xA14A,
    0xB16B,
    0xC18C,
    0xD1AD,
    0xE1CE,
    0xF1EF,
    0x1231,
    0x0210,
    0x3273,
    0x2252,
    0x52B5,
    0x4294,
    0x72F7,
    0x62D6,
    0x9339,
    0x8318,
    0xB37B,
    0xA35A,
    0xD3BD,
    0xC39C,
    0xF3FF,
    0xE3DE,
    0x2462,
    0x3443,
    0x0420,
    0x1401,
    0x64E6,
    0x74C7,
    0x44A4,
    0x5485,
    0xA56A,
    0xB54B,
    0x8528,
    0x9509,
    0xE5EE,
    0xF5CF,
    0xC5AC,
    0xD58D,
    0x3653,
    0x2672,
    0x1611,
    0x0630,
    0x76D7,
    0x66F6,
    0x5695,
    0x46B4,
    0xB75B,
    0xA77A,
    0x9719,
    0x8738,
    0xF7DF,
    0xE7FE,
    0xD79D,
    0xC7BC,
    0x48C4,
    0x58E5,
    0x6886,
    0x78A7,
    0x0840,
    0x1861,
    0x2802,
    0x3823,
    0xC9CC,
    0xD9ED,
    0xE98E,
    0xF9AF,
    0x8948,
    0x9969,
    0xA90A,
    0xB92B,
    0x5AF5,
    0x4AD4,
    0x7AB7,
    0x6A96,
    0x1A71,
    0x0A50,
    0x3A33,
    0x2A12,
    0xDBFD,
    0xCBDC,
    0xFBBF,
    0xEB9E,
    0x9B79,
    0x8B58,
    0xBB3B,
    0xAB1A,
    0x6CA6,
    0x7C87,
    0x4CE4,
    0x5CC5,
    0x2C22,
    0x3C03,
    0x0C60,
    0x1C41,
    0xEDAE,
    0xFD8F,
    0xCDEC,
    0xDDCD,
    0xAD2A,
    0xBD0B,
    0x8D68,
    0x9D49,
    0x7E97,
    0x6EB6,
    0x5ED5,
    0x4EF4,
    0x3E13,
    0x2E32,
    0x1E51,
    0x0E70,
    0xFF9F,
    0xEFBE,
    0xDFDD,
    0xCFFC,
    0xBF1B,
    0xAF3A,
    0x9F59,
    0x8F78,
    0x9188,
    0x81A9,
    0xB1CA,
    0xA1EB,
    0xD10C,
    0xC12D,
    0xF14E,
    0xE16F,
    0x1080,
    0x00A1,
    0x30C2,
    0x20E3,
    0x5004,
    0x4025,
    0x7046,
    0x6067,
    0x83B9,
    0x9398,
    0xA3FB,
    0xB3DA,
    0xC33D,
    0xD31C,
    0xE37F,
    0xF35E,
    0x02B1,
    0x1290,
    0x22F3,
    0x32D2,
    0x4235,
    0x5214,
    0x6277,
    0x7256,
    0xB5EA,
    0xA5CB,
    0x95A8,
    0x8589,
    0xF56E,
    0xE54F,
    0xD52C,
    0xC50D,
    0x34E2,
    0x24C3,
    0x14A0,
    0x0481,
    0x7466,
    0x6447,
    0x5424,
    0x4405,
    0xA7DB,
    0xB7FA,
    0x8799,
    0x97B8,
    0xE75F,
    0xF77E,
    0xC71D,
    0xD73C,
    0x26D3,
    0x36F2,
    0x0691,
    0x16B0,
    0x6657,
    0x7676,
    0x4615,
    0x5634,
    0xD94C,
    0xC96D,
    0xF90E,
    0xE92F,
    0x99C8,
    0x89E9,
    0xB98A,
    0xA9AB,
    0x5844,
    0x4865,
    0x7806,
    0x6827,
    0x18C0,
    0x08E1,
    0x3882,
    0x28A3,
    0xCB7D,
    0xDB5C,
    0xEB3F,
    0xFB1E,
    0x8BF9,
    0x9BD8,
    0xABBB,
    0xBB9A,
    0x4A75,
    0x5A54,
    0x6A37,
    0x7A16,
    0x0AF1,
    0x1AD0,
    0x2AB3,
    0x3A92,
    0xFD2E,
    0xED0F,
    0xDD6C,
    0xCD4D,
    0xBDAA,
    0xAD8B,
    0x9DE8,
    0x8DC9,
    0x7C26,
    0x6C07,
    0x5C64,
    0x4C45,
    0x3CA2,
    0x2C83,
    0x1CE0,
    0x0CC1,
    0xEF1F,
    0xFF3E,
    0xCF5D,
    0xDF7C,
    0xAF9B,
    0xBFBA,
    0x8FD9,
    0x9FF8,
    0x6E17,
    0x7E36,
    0x4E55,
    0x5E74,
    0x2E93,
    0x3EB2,
    0x0ED1,
    0x1EF0,
)

# Compile-time assertion
assert len(CRC16_TABLE) == 256, "CRC16_TABLE must have exactly 256 entries"

# =============================================================================
# Default Network Endpoints
# =============================================================================

DEFAULT_IP: Final[str] = "192.168.144.25"
DEFAULT_UDP_PORT: Final[int] = 37260
DEFAULT_TCP_PORT: Final[int] = 37260
DEFAULT_BAUD: Final[int] = 115200
DEFAULT_HTTP_PORT: Final[int] = 82

# =============================================================================
# Pre-built Frames
# =============================================================================

# TCP heartbeat packet (from spec: 55 66 01 01 00 00 00 00 00 59 8B)
HEARTBEAT_FRAME: Final[bytes] = bytes.fromhex("556601010000000000598B")

# =============================================================================
# Camera Constants
# =============================================================================

CAMERA_BOOT_SECONDS: Final[int] = 30

# =============================================================================
# Laser Ranging Constants
# =============================================================================

LASER_MIN_M: Final[int] = 5
LASER_MAX_M: Final[int] = 1200
LASER_MIN_RAW_DM: Final[int] = 50  # Minimum raw value in decimeters

# =============================================================================
# Command IDs (from SIYI SDK Protocol Appendix B)
# =============================================================================

CMD_TCP_HEARTBEAT: Final[int] = 0x00
CMD_REQUEST_FIRMWARE_VERSION: Final[int] = 0x01
CMD_REQUEST_HARDWARE_ID: Final[int] = 0x02
CMD_AUTO_FOCUS: Final[int] = 0x04
CMD_MANUAL_ZOOM_AUTO_FOCUS: Final[int] = 0x05
CMD_MANUAL_FOCUS: Final[int] = 0x06
CMD_GIMBAL_ROTATION: Final[int] = 0x07
CMD_ONE_KEY_CENTERING: Final[int] = 0x08
CMD_REQUEST_CAMERA_SYSTEM_INFO: Final[int] = 0x0A
CMD_FUNCTION_FEEDBACK: Final[int] = 0x0B
CMD_CAPTURE_PHOTO_RECORD_VIDEO: Final[int] = 0x0C
CMD_REQUEST_GIMBAL_ATTITUDE: Final[int] = 0x0D
CMD_SET_GIMBAL_ATTITUDE: Final[int] = 0x0E
CMD_ABSOLUTE_ZOOM_AUTO_FOCUS: Final[int] = 0x0F
CMD_REQUEST_VIDEO_STITCHING_MODE: Final[int] = 0x10
CMD_SET_VIDEO_STITCHING_MODE: Final[int] = 0x11
CMD_GET_TEMP_AT_POINT: Final[int] = 0x12
CMD_LOCAL_TEMP_MEASUREMENT: Final[int] = 0x13
CMD_GLOBAL_TEMP_MEASUREMENT: Final[int] = 0x14
CMD_REQUEST_LASER_DISTANCE: Final[int] = 0x15
CMD_REQUEST_ZOOM_RANGE: Final[int] = 0x16
CMD_REQUEST_LASER_LATLON: Final[int] = 0x17
CMD_REQUEST_ZOOM_MAGNIFICATION: Final[int] = 0x18
CMD_REQUEST_GIMBAL_MODE: Final[int] = 0x19
CMD_REQUEST_PSEUDO_COLOR: Final[int] = 0x1A
CMD_SET_PSEUDO_COLOR: Final[int] = 0x1B
CMD_REQUEST_ENCODING_PARAMS: Final[int] = 0x20
CMD_SET_ENCODING_PARAMS: Final[int] = 0x21
CMD_SEND_AIRCRAFT_ATTITUDE: Final[int] = 0x22
CMD_SEND_RC_CHANNELS: Final[int] = 0x23
CMD_REQUEST_FC_DATA_STREAM: Final[int] = 0x24
CMD_REQUEST_GIMBAL_DATA_STREAM: Final[int] = 0x25
CMD_REQUEST_MAGNETIC_ENCODER: Final[int] = 0x26
CMD_REQUEST_CONTROL_MODE: Final[int] = 0x27
CMD_REQUEST_WEAK_THRESHOLD: Final[int] = 0x28
CMD_SET_WEAK_THRESHOLD: Final[int] = 0x29
CMD_REQUEST_MOTOR_VOLTAGE: Final[int] = 0x2A
CMD_SET_UTC_TIME: Final[int] = 0x30
CMD_REQUEST_GIMBAL_SYSTEM_INFO: Final[int] = 0x31
CMD_SET_LASER_RANGING_STATE: Final[int] = 0x32
CMD_REQUEST_THERMAL_OUTPUT_MODE: Final[int] = 0x33
CMD_SET_THERMAL_OUTPUT_MODE: Final[int] = 0x34
CMD_GET_SINGLE_TEMP_FRAME: Final[int] = 0x35
CMD_REQUEST_THERMAL_GAIN: Final[int] = 0x37
CMD_SET_THERMAL_GAIN: Final[int] = 0x38
CMD_REQUEST_ENV_CORRECTION_PARAMS: Final[int] = 0x39
CMD_SET_ENV_CORRECTION_PARAMS: Final[int] = 0x3A
CMD_REQUEST_ENV_CORRECTION_SWITCH: Final[int] = 0x3B
CMD_SET_ENV_CORRECTION_SWITCH: Final[int] = 0x3C
CMD_SEND_RAW_GPS: Final[int] = 0x3E
CMD_REQUEST_SYSTEM_TIME: Final[int] = 0x40
CMD_SINGLE_AXIS_ATTITUDE: Final[int] = 0x41
CMD_GET_IR_THRESH_MAP_STA: Final[int] = 0x42
CMD_SET_IR_THRESH_MAP_STA: Final[int] = 0x43
CMD_GET_IR_THRESH_PARAM: Final[int] = 0x44
CMD_SET_IR_THRESH_PARAM: Final[int] = 0x45
CMD_GET_IR_THRESH_PRECISION: Final[int] = 0x46
CMD_SET_IR_THRESH_PRECISION: Final[int] = 0x47
CMD_SD_FORMAT: Final[int] = 0x48
CMD_GET_PIC_NAME_TYPE: Final[int] = 0x49
CMD_SET_PIC_NAME_TYPE: Final[int] = 0x4A
CMD_GET_MAVLINK_OSD_FLAG: Final[int] = 0x4B
CMD_SET_MAVLINK_OSD_FLAG: Final[int] = 0x4C
CMD_GET_AI_MODE_STA: Final[int] = 0x4D
CMD_GET_AI_TRACK_STREAM_STA: Final[int] = 0x4E
CMD_MANUAL_THERMAL_SHUTTER: Final[int] = 0x4F
CMD_AI_TRACK_STREAM: Final[int] = 0x50
CMD_SET_AI_TRACK_STREAM_STA: Final[int] = 0x51
CMD_REQUEST_WEAK_CONTROL_MODE: Final[int] = 0x70
CMD_SET_WEAK_CONTROL_MODE: Final[int] = 0x71
CMD_SOFT_REBOOT: Final[int] = 0x80
CMD_GET_IP: Final[int] = 0x81
CMD_SET_IP: Final[int] = 0x82

# =============================================================================
# Hardware ID Product Codes (first byte of hardware ID)
# =============================================================================

HW_ID_ZR10: Final[int] = 0x6B
HW_ID_A8_MINI: Final[int] = 0x73
HW_ID_A2_MINI: Final[int] = 0x75
HW_ID_ZR30: Final[int] = 0x78
HW_ID_QUAD_SPECTRUM: Final[int] = 0x7A

# =============================================================================
# A8 mini mechanical limits (degrees)
# =============================================================================
# Source: SIYI A8 mini user manual. Yaw is symmetric; pitch is asymmetric
# (more travel down than up).

A8MINI_YAW_MIN_DEG: Final[float] = -135.0
A8MINI_YAW_MAX_DEG: Final[float] = 135.0
A8MINI_PITCH_MIN_DEG: Final[float] = -90.0
A8MINI_PITCH_MAX_DEG: Final[float] = 25.0

# Velocity command range for CMD 0x07 (gimbal rotation).
GIMBAL_RATE_CMD_MIN: Final[int] = -100
GIMBAL_RATE_CMD_MAX: Final[int] = 100
