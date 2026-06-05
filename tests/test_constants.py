# Copyright (c) 2026 Mohamed Abdelkader <mohamedashraf123@gmail.com>
# All rights reserved.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

"""Tests for siyi_sdk.constants module."""

from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

from siyi_sdk import constants
from siyi_sdk.protocol.crc import crc16


class TestFrameConstants:
    """Test frame structure constants."""

    def test_stx_value(self):
        """STX should be 0x6655."""
        assert constants.STX == 0x6655

    def test_stx_bytes(self):
        """STX_BYTES should be little-endian wire format."""
        assert constants.STX_BYTES == b"\x55\x66"

    def test_ctrl_flags(self):
        """CTRL flags should match SIYI protocol bit-field spec."""
        assert constants.CTRL_NEED_ACK == 0x01  # bit[0]: sender needs response
        assert constants.CTRL_ACK_PACK == 0x02  # bit[1]: this frame is a response

    def test_frame_lengths(self):
        """Frame length constants should be correct."""
        assert constants.HEADER_LEN == 8
        assert constants.CRC_LEN == 2
        assert constants.MIN_FRAME_LEN == 10

    def test_seq_max(self):
        """SEQ_MAX should be 0xFFFF."""
        assert constants.SEQ_MAX == 0xFFFF


class TestCRCConstants:
    """Test CRC-related constants."""

    def test_crc_poly(self):
        """CRC polynomial should be 0x1021 (XMODEM)."""
        assert constants.CRC16_POLY == 0x1021

    def test_crc_init(self):
        """CRC initial value should be 0x0000."""
        assert constants.CRC16_INIT == 0x0000

    def test_crc_table_length(self):
        """CRC table should have exactly 256 entries."""
        assert len(constants.CRC16_TABLE) == 256

    def test_crc_table_values_in_range(self):
        """All CRC table values should be 16-bit."""
        for i, value in enumerate(constants.CRC16_TABLE):
            assert 0 <= value <= 0xFFFF, f"CRC16_TABLE[{i}] = {value} out of range"

    def test_crc_table_first_entry(self):
        """First CRC table entry should be 0x0000."""
        assert constants.CRC16_TABLE[0] == 0x0000

    def test_crc_table_second_entry(self):
        """Second CRC table entry should be 0x1021 (polynomial)."""
        assert constants.CRC16_TABLE[1] == 0x1021


class TestNetworkDefaults:
    """Test default network endpoints."""

    def test_default_ip(self):
        """Default IP should be 192.168.144.25."""
        assert constants.DEFAULT_IP == "192.168.144.25"

    def test_default_udp_port(self):
        """Default UDP port should be 37260."""
        assert constants.DEFAULT_UDP_PORT == 37260

    def test_default_tcp_port(self):
        """Default TCP port should be 37260."""
        assert constants.DEFAULT_TCP_PORT == 37260

    def test_default_baud(self):
        """Default baud rate should be 115200."""
        assert constants.DEFAULT_BAUD == 115200


class TestHeartbeatFrame:
    """Test pre-built heartbeat frame."""

    def test_heartbeat_frame_length(self):
        """Heartbeat frame should be 11 bytes."""
        assert len(constants.HEARTBEAT_FRAME) == 11

    def test_heartbeat_frame_stx(self):
        """Heartbeat frame should start with STX."""
        assert constants.HEARTBEAT_FRAME[:2] == constants.STX_BYTES

    def test_heartbeat_frame_cmd_id(self):
        """Heartbeat frame should have CMD_ID 0x00."""
        assert constants.HEARTBEAT_FRAME[7] == 0x00

    def test_heartbeat_frame_crc_valid(self):
        """Heartbeat frame CRC should be valid."""
        frame_without_crc = constants.HEARTBEAT_FRAME[:-2]
        crc_bytes = constants.HEARTBEAT_FRAME[-2:]
        expected_crc = int.from_bytes(crc_bytes, "little")
        actual_crc = crc16(frame_without_crc)
        assert expected_crc == actual_crc


class TestLaserConstants:
    """Test laser ranging constants."""

    def test_laser_min_m(self):
        """Laser minimum distance should be 5m."""
        assert constants.LASER_MIN_M == 5

    def test_laser_max_m(self):
        """Laser maximum distance should be 1200m."""
        assert constants.LASER_MAX_M == 1200

    def test_laser_min_raw_dm(self):
        """Laser minimum raw value should be 50 dm."""
        assert constants.LASER_MIN_RAW_DM == 50


class TestCommandIDs:
    """Test command ID constants."""

    def test_all_cmd_ids_unique(self):
        """All CMD_ID values should be unique."""
        cmd_ids = [
            constants.CMD_TCP_HEARTBEAT,
            constants.CMD_REQUEST_FIRMWARE_VERSION,
            constants.CMD_REQUEST_HARDWARE_ID,
            constants.CMD_AUTO_FOCUS,
            constants.CMD_MANUAL_ZOOM_AUTO_FOCUS,
            constants.CMD_MANUAL_FOCUS,
            constants.CMD_GIMBAL_ROTATION,
            constants.CMD_ONE_KEY_CENTERING,
            constants.CMD_REQUEST_CAMERA_SYSTEM_INFO,
            constants.CMD_FUNCTION_FEEDBACK,
            constants.CMD_CAPTURE_PHOTO_RECORD_VIDEO,
            constants.CMD_REQUEST_GIMBAL_ATTITUDE,
            constants.CMD_SET_GIMBAL_ATTITUDE,
            constants.CMD_ABSOLUTE_ZOOM_AUTO_FOCUS,
            constants.CMD_REQUEST_VIDEO_STITCHING_MODE,
            constants.CMD_SET_VIDEO_STITCHING_MODE,
            constants.CMD_GET_TEMP_AT_POINT,
            constants.CMD_LOCAL_TEMP_MEASUREMENT,
            constants.CMD_GLOBAL_TEMP_MEASUREMENT,
            constants.CMD_REQUEST_LASER_DISTANCE,
            constants.CMD_REQUEST_ZOOM_RANGE,
            constants.CMD_REQUEST_LASER_LATLON,
            constants.CMD_REQUEST_ZOOM_MAGNIFICATION,
            constants.CMD_REQUEST_GIMBAL_MODE,
            constants.CMD_REQUEST_PSEUDO_COLOR,
            constants.CMD_SET_PSEUDO_COLOR,
            constants.CMD_REQUEST_ENCODING_PARAMS,
            constants.CMD_SET_ENCODING_PARAMS,
            constants.CMD_SEND_AIRCRAFT_ATTITUDE,
            constants.CMD_SEND_RC_CHANNELS,
            constants.CMD_REQUEST_FC_DATA_STREAM,
            constants.CMD_REQUEST_GIMBAL_DATA_STREAM,
            constants.CMD_REQUEST_MAGNETIC_ENCODER,
            constants.CMD_REQUEST_CONTROL_MODE,
            constants.CMD_REQUEST_WEAK_THRESHOLD,
            constants.CMD_SET_WEAK_THRESHOLD,
            constants.CMD_REQUEST_MOTOR_VOLTAGE,
            constants.CMD_SET_UTC_TIME,
            constants.CMD_REQUEST_GIMBAL_SYSTEM_INFO,
            constants.CMD_SET_LASER_RANGING_STATE,
            constants.CMD_REQUEST_THERMAL_OUTPUT_MODE,
            constants.CMD_SET_THERMAL_OUTPUT_MODE,
            constants.CMD_GET_SINGLE_TEMP_FRAME,
            constants.CMD_REQUEST_THERMAL_GAIN,
            constants.CMD_SET_THERMAL_GAIN,
            constants.CMD_REQUEST_ENV_CORRECTION_PARAMS,
            constants.CMD_SET_ENV_CORRECTION_PARAMS,
            constants.CMD_REQUEST_ENV_CORRECTION_SWITCH,
            constants.CMD_SET_ENV_CORRECTION_SWITCH,
            constants.CMD_SEND_RAW_GPS,
            constants.CMD_REQUEST_SYSTEM_TIME,
            constants.CMD_SINGLE_AXIS_ATTITUDE,
            constants.CMD_GET_IR_THRESH_MAP_STA,
            constants.CMD_SET_IR_THRESH_MAP_STA,
            constants.CMD_GET_IR_THRESH_PARAM,
            constants.CMD_SET_IR_THRESH_PARAM,
            constants.CMD_GET_IR_THRESH_PRECISION,
            constants.CMD_SET_IR_THRESH_PRECISION,
            constants.CMD_SD_FORMAT,
            constants.CMD_GET_PIC_NAME_TYPE,
            constants.CMD_SET_PIC_NAME_TYPE,
            constants.CMD_GET_MAVLINK_OSD_FLAG,
            constants.CMD_SET_MAVLINK_OSD_FLAG,
            constants.CMD_GET_AI_MODE_STA,
            constants.CMD_GET_AI_TRACK_STREAM_STA,
            constants.CMD_MANUAL_THERMAL_SHUTTER,
            constants.CMD_AI_TRACK_STREAM,
            constants.CMD_SET_AI_TRACK_STREAM_STA,
            constants.CMD_REQUEST_WEAK_CONTROL_MODE,
            constants.CMD_SET_WEAK_CONTROL_MODE,
            constants.CMD_SOFT_REBOOT,
            constants.CMD_GET_IP,
            constants.CMD_SET_IP,
        ]
        assert len(set(cmd_ids)) == len(cmd_ids), "Duplicate CMD_ID values found"

    def test_cmd_heartbeat(self):
        """TCP heartbeat CMD_ID should be 0x00."""
        assert constants.CMD_TCP_HEARTBEAT == 0x00

    def test_cmd_firmware_version(self):
        """Request firmware version CMD_ID should be 0x01."""
        assert constants.CMD_REQUEST_FIRMWARE_VERSION == 0x01

    def test_cmd_hardware_id(self):
        """Request hardware ID CMD_ID should be 0x02."""
        assert constants.CMD_REQUEST_HARDWARE_ID == 0x02


class TestHardwareIDs:
    """Test hardware ID constants."""

    def test_hw_id_zr10(self):
        """ZR10 hardware ID should be 0x6B."""
        assert constants.HW_ID_ZR10 == 0x6B

    def test_hw_id_a8_mini(self):
        """A8 Mini hardware ID should be 0x73."""
        assert constants.HW_ID_A8_MINI == 0x73

    def test_hw_id_a2_mini(self):
        """A2 Mini hardware ID should be 0x75."""
        assert constants.HW_ID_A2_MINI == 0x75

    def test_hw_id_zr30(self):
        """ZR30 hardware ID should be 0x78."""
        assert constants.HW_ID_ZR30 == 0x78

    def test_hw_id_quad_spectrum(self):
        """Quad Spectrum hardware ID should be 0x7A."""
        assert constants.HW_ID_QUAD_SPECTRUM == 0x7A


class TestA8MiniLimits:
    """Test A8 mini mechanical limit constants."""

    def test_yaw_limits_symmetric(self):
        assert constants.A8MINI_YAW_MIN_DEG == -135.0
        assert constants.A8MINI_YAW_MAX_DEG == 135.0

    def test_pitch_limits_asymmetric(self):
        # Pitch is asymmetric: more down travel than up.
        assert constants.A8MINI_PITCH_MIN_DEG == -90.0
        assert constants.A8MINI_PITCH_MAX_DEG == 25.0
        assert constants.A8MINI_PITCH_MIN_DEG < constants.A8MINI_PITCH_MAX_DEG

    def test_rate_command_range(self):
        assert constants.GIMBAL_RATE_CMD_MIN == -100
        assert constants.GIMBAL_RATE_CMD_MAX == 100


class TestNoMagicHexLiterals:
    """Test that hex literals only appear in constants.py."""

    def test_no_magic_hex_in_other_modules(self):
        """Hex literals >2 digits should only appear in constants.py or comments/docstrings."""
        siyi_sdk_path = Path(__file__).parent.parent / "siyi_sdk"

        # Pattern for hex literals with 3+ hex digits (likely magic numbers)
        hex_pattern = re.compile(r"0x[0-9A-Fa-f]{3,}")

        violations = []

        for py_file in siyi_sdk_path.glob("**/*.py"):
            if py_file.name == "constants.py":
                continue

            try:
                source = py_file.read_text()
                tree = ast.parse(source)
            except (SyntaxError, UnicodeDecodeError):
                continue

            # Walk the AST to find hex literals in code (not comments/docstrings)
            for node in ast.walk(tree):
                if (
                    isinstance(node, ast.Constant)
                    and isinstance(node.value, int)
                    and node.value > 0xFF
                ):
                    # Check if this looks like a hex literal in the source
                    line = source.split("\n")[node.lineno - 1] if node.lineno else ""
                    hex_matches = hex_pattern.findall(line)
                    for match in hex_matches:
                        # Allow common masks (case-insensitive comparison)
                        if match.lower() not in ["0xffff", "0x0000"]:
                            # Check it's not in a comment
                            comment_start = line.find("#")
                            match_pos = line.find(match)
                            if comment_start == -1 or match_pos < comment_start:
                                rel_path = py_file.relative_to(siyi_sdk_path)
                                violations.append(f"{rel_path}:{node.lineno}: {match}")

        # This test is informational - we allow some patterns
        # Just ensure we don't have obvious protocol constants outside constants.py
        for v in violations:
            # Filter out test files and known acceptable patterns
            if "test" not in v.lower():
                pytest.fail(f"Possible magic hex literal: {v}")
