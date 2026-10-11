# Copyright (c) 2026 Mohamed Abdelkader <mohamedashraf123@gmail.com>
# All rights reserved.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

"""Data models for the SIYI SDK protocol.

This module contains all enumerations and dataclasses representing
protocol-level data structures from the SIYI SDK specification.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
from ipaddress import IPv4Address
from typing import Final

# =============================================================================
# Product and Hardware Enumerations
# =============================================================================


class ProductID(IntEnum):
    """Product identification codes (first byte of hardware ID)."""

    ZR10 = 0x6B
    A8_MINI = 0x73
    A2_MINI = 0x75
    ZR30 = 0x78
    QUAD_SPECTRUM = 0x7A

    @property
    def label(self) -> str:
        """Human-readable product name (e.g. 'A8 Mini')."""
        _labels: dict[int, str] = {
            0x6B: "ZR10",
            0x73: "A8 Mini",
            0x75: "A2 Mini",
            0x78: "ZR30",
            0x7A: "Quad Spectrum",
        }
        return _labels.get(self.value, self.name)


# =============================================================================
# Gimbal Mode Enumerations
# =============================================================================


class GimbalMotionMode(IntEnum):
    """Gimbal motion mode."""

    LOCK = 0
    FOLLOW = 1
    FPV = 2


class MountingDirection(IntEnum):
    """Gimbal mounting direction."""

    RESERVED = 0
    NORMAL = 1
    INVERTED = 2


class CenteringAction(IntEnum):
    """One-key centering action types.

    To level the camera use ONE_KEY_CENTER. An A8 mini acks CENTER (3) with
    success but does not move the camera back from pitch -90.
    """

    ONE_KEY_CENTER = 1
    CENTER_DOWNWARD = 2
    CENTER = 3
    DOWNWARD = 4


class ControlMode(IntEnum):
    """Gimbal control mode (ArduPilot debugging)."""

    ATTITUDE = 0
    WEAK = 1
    MIDDLE = 2
    FPV = 3
    MOTOR_CLOSE = 4


# =============================================================================
# Video and Recording Enumerations
# =============================================================================


class HDMICVBSOutput(IntEnum):
    """HDMI/CVBS video output status."""

    HDMI_ON_CVBS_OFF = 0
    HDMI_OFF_CVBS_ON = 1


class RecordingState(IntEnum):
    """Recording status."""

    NOT_RECORDING = 0
    RECORDING = 1
    NO_TF_CARD = 2
    DATA_LOSS = 3


class FunctionFeedback(IntEnum):
    """Function feedback response codes."""

    PHOTO_OK = 0
    PHOTO_FAILED = 1
    HDR_ON = 2
    HDR_OFF = 3
    RECORDING_FAILED = 4
    RECORDING_STARTED = 5
    RECORDING_STOPPED = 6


class CaptureFuncType(IntEnum):
    """Capture photo / record video function types."""

    PHOTO = 0
    HDR_TOGGLE = 1
    START_RECORD = 2
    LOCK_MODE = 3
    FOLLOW_MODE = 4
    FPV_MODE = 5
    ENABLE_HDMI = 6
    ENABLE_CVBS = 7
    DISABLE_HDMI_CVBS = 8
    TILT_DOWNWARD = 9
    ZOOM_LINKAGE = 10


class VideoEncType(IntEnum):
    """Video encoding type."""

    H264 = 1
    H265 = 2


class StreamType(IntEnum):
    """Video stream type."""

    RECORDING = 0
    MAIN = 1
    SUB = 2


class VideoStitchingMode(IntEnum):
    """Video stitching mode (for multi-sensor cameras)."""

    MODE_0 = 0  # Stitching: Main=Zoom&Thermal, Sub=Wide
    MODE_1 = 1  # Stitching: Main=Wide&Thermal, Sub=Zoom
    MODE_2 = 2  # Stitching: Main=Zoom&Wide, Sub=Thermal
    MODE_3 = 3  # Non-stitching: Main=Zoom, Sub=Thermal
    MODE_4 = 4  # Non-stitching: Main=Zoom, Sub=Wide
    MODE_5 = 5  # Non-stitching: Main=Wide, Sub=Thermal
    MODE_6 = 6  # Non-stitching: Main=Wide, Sub=Zoom
    MODE_7 = 7  # Non-stitching: Main=Thermal, Sub=Zoom
    MODE_8 = 8  # Non-stitching: Main=Thermal, Sub=Wide


# =============================================================================
# Thermal Imaging Enumerations
# =============================================================================


class PseudoColor(IntEnum):
    """Thermal imaging pseudo-color palette."""

    WHITE_HOT = 0
    RESERVED = 1
    SEPIA = 2
    IRONBOW = 3
    RAINBOW = 4
    NIGHT = 5
    AURORA = 6
    RED_HOT = 7
    JUNGLE = 8
    MEDICAL = 9
    BLACK_HOT = 10
    GLORY_HOT = 11


class TempMeasureFlag(IntEnum):
    """Temperature measurement mode flag."""

    DISABLE = 0
    MEASURE_ONCE = 1
    CONTINUOUS_5HZ = 2


class ThermalOutputMode(IntEnum):
    """Thermal imaging output mode."""

    FPS30 = 0
    FPS25_PLUS_TEMP = 1


class ThermalGain(IntEnum):
    """Thermal imaging gain mode."""

    LOW = 0
    HIGH = 1


class IRThreshPrecision(IntEnum):
    """IR threshold precision level."""

    MAX = 1
    MID = 2
    MIN = 3


# =============================================================================
# Data Stream Enumerations
# =============================================================================


class FCDataType(IntEnum):
    """Flight controller data stream type."""

    ATTITUDE = 1
    RC_CHANNELS = 2


class GimbalDataType(IntEnum):
    """Gimbal data stream type."""

    ATTITUDE = 1
    LASER_RANGE = 2
    MAGNETIC_ENCODER = 3
    MOTOR_VOLTAGE = 4


class DataStreamFreq(IntEnum):
    """Data stream output frequency."""

    OFF = 0
    HZ2 = 1
    HZ4 = 2
    HZ5 = 3
    HZ10 = 4
    HZ20 = 5
    HZ50 = 6
    HZ100 = 7


# =============================================================================
# AI Tracking Enumerations
# =============================================================================


class AITargetID(IntEnum):
    """AI tracking target identification."""

    HUMAN = 0
    CAR = 1
    BUS = 2
    TRUCK = 3
    ANY = 255


class AITrackStatus(IntEnum):
    """AI tracking status."""

    NORMAL_AI = 0
    INTERMITTENT_LOSS = 1
    LOST = 2
    USER_CANCELED = 3
    NORMAL_ANY = 4


class AIStreamStatus(IntEnum):
    """AI tracking coordinate stream status."""

    DISABLED = 0
    STREAMING = 1
    AI_NOT_ENABLED = 2
    TRACKING_NOT_ENABLED = 3


# =============================================================================
# File System Enumerations
# =============================================================================


class FileType(IntEnum):
    """File type for naming conventions."""

    PICTURE = 0
    TEMP_RAW = 1
    RECORD_VIDEO = 2


class FileNameType(IntEnum):
    """File naming convention type."""

    RESERVE = 0
    INDEX = 1
    TIMESTAMP = 2


# Alias for backwards compatibility
PicName = FileNameType


# =============================================================================
# Firmware and Hardware Dataclasses
# =============================================================================


@dataclass(frozen=True, slots=True)
class FirmwareVersion:
    """Firmware version information.

    Attributes:
        camera: Camera firmware version as packed uint32.
        gimbal: Gimbal firmware version as packed uint32.
        zoom: Zoom module firmware version as packed uint32.

    """

    camera: int
    gimbal: int
    zoom: int

    @staticmethod
    def decode_word(word: int) -> tuple[int, int, int]:
        """Decode a firmware version word into major, minor, patch.

        The high byte is ignored per spec note. The low 3 bytes are
        (from LSB to MSB): patch, minor, major.

        Args:
            word: Raw uint32 firmware version word.

        Returns:
            Tuple of (major, minor, patch) version numbers.

        Example:
            >>> FirmwareVersion.decode_word(0x6E030203)
            (2, 2, 3)

        """
        patch = word & 0xFF
        minor = (word >> 8) & 0xFF
        major = (word >> 16) & 0xFF
        return (major, minor, patch)

    @staticmethod
    def format_word(word: int) -> str:
        """Format a firmware version word as a human-readable string.

        Args:
            word: Raw uint32 firmware version word. Zero means not present.

        Returns:
            String like 'v3.3.0', or 'n/a' if word is 0.

        """
        if word == 0:
            return "n/a"
        major, minor, patch = FirmwareVersion.decode_word(word)
        return f"v{major}.{minor}.{patch}"


@dataclass(frozen=True, slots=True)
class HardwareID:
    """Hardware identification.

    Attributes:
        raw: Raw 12-byte hardware ID string.

    """

    raw: bytes

    @property
    def product_id(self) -> ProductID:
        """Get the product identification from the first two bytes.

        The hardware ID is a 12-byte ASCII string. The first two characters
        are the product code in ASCII hex (e.g. b"73..." -> 0x73 = A8 Mini).

        Returns:
            ProductID enumeration value.

        Raises:
            ValueError: If the code is not a known product ID.

        """
        code = int(self.raw[0:2], 16)
        return ProductID(code)


# =============================================================================
# Camera System Information
# =============================================================================


@dataclass(frozen=True, slots=True)
class CameraSystemInfo:
    """Camera system information (0x0A response).

    Attributes:
        reserved_a: First reserved byte.
        hdr_sta: HDR status (0=off, 1=on).
        reserved_b: Second reserved byte.
        record_sta: Recording state.
        gimbal_motion_mode: Current gimbal motion mode.
        gimbal_mounting_dir: Gimbal mounting direction.
        video_hdmi_or_cvbs: HDMI/CVBS output status.
        zoom_linkage: Zoom linkage switch (0=off, 1=on).

    """

    reserved_a: int
    hdr_sta: int
    reserved_b: int
    record_sta: RecordingState
    gimbal_motion_mode: GimbalMotionMode
    gimbal_mounting_dir: MountingDirection
    video_hdmi_or_cvbs: HDMICVBSOutput
    zoom_linkage: int


# =============================================================================
# Attitude and Motion Dataclasses
# =============================================================================


@dataclass(frozen=True, slots=True)
class GimbalAttitude:
    """Gimbal attitude data (0x0D response).

    All angles are in degrees and rates in degrees per second.
    Raw int16 values are divided by 10.

    Attributes:
        yaw_deg: Yaw angle in degrees.
        pitch_deg: Pitch angle in degrees.
        roll_deg: Roll angle in degrees.
        yaw_rate_dps: Yaw angular velocity in degrees/second.
        pitch_rate_dps: Pitch angular velocity in degrees/second.
        roll_rate_dps: Roll angular velocity in degrees/second.

    """

    yaw_deg: float
    pitch_deg: float
    roll_deg: float
    yaw_rate_dps: float
    pitch_rate_dps: float
    roll_rate_dps: float


@dataclass(frozen=True, slots=True)
class SetAttitudeAck:
    """Set attitude acknowledgment (0x0E response).

    All angles are in degrees. Raw int16 values are divided by 10.

    Attributes:
        yaw_deg: Current yaw angle in degrees.
        pitch_deg: Current pitch angle in degrees.
        roll_deg: Current roll angle in degrees.

    """

    yaw_deg: float
    pitch_deg: float
    roll_deg: float


@dataclass(frozen=True, slots=True)
class AircraftAttitude:
    """Aircraft attitude data (0x22 send format).

    All angles are in radians and rates in radians per second.

    Attributes:
        time_boot_ms: Timestamp since system boot in milliseconds.
        roll_rad: Roll angle in radians (-pi to +pi).
        pitch_rad: Pitch angle in radians (-pi/2 to +pi/2).
        yaw_rad: Yaw angle in radians (-pi to +pi).
        rollspeed: Roll angular speed in rad/s.
        pitchspeed: Pitch angular speed in rad/s.
        yawspeed: Yaw angular speed in rad/s.

    """

    time_boot_ms: int
    roll_rad: float
    pitch_rad: float
    yaw_rad: float
    rollspeed: float
    pitchspeed: float
    yawspeed: float


@dataclass(frozen=True, slots=True)
class RCChannels:
    """RC channel data (0x23 send format).

    Attributes:
        chans: Tuple of 18 channel values in microseconds.
        chancount: Total number of RC channels being received.
        rssi: Receive signal strength indicator (0-254, 255=unknown).

    """

    chans: tuple[int, ...]
    chancount: int
    rssi: int


@dataclass(frozen=True, slots=True)
class MagneticEncoderAngles:
    """Magnetic encoder angle data (0x26 response).

    All angles in degrees. Raw int16 values are divided by 10.

    Attributes:
        yaw: Yaw angle in degrees.
        pitch: Pitch angle in degrees.
        roll: Roll angle in degrees.

    """

    yaw: float
    pitch: float
    roll: float


@dataclass(frozen=True, slots=True)
class MotorVoltage:
    """Motor voltage data (0x2A response).

    All voltages in volts. Raw int16 values are divided by 1000.

    Attributes:
        yaw: Yaw motor voltage in volts.
        pitch: Pitch motor voltage in volts.
        roll: Roll motor voltage in volts.

    """

    yaw: float
    pitch: float
    roll: float


@dataclass(frozen=True, slots=True)
class WeakControlThreshold:
    """Weak control threshold data (0x28 response).

    All values have one decimal place precision.

    Attributes:
        limit: Weak control mode voltage limit (1.0-5.0).
        voltage: Voltage threshold (2.0-5.0).
        angular_error: Angular error threshold (3.0-30.0).

    """

    limit: float
    voltage: float
    angular_error: float


# =============================================================================
# Video Encoding
# =============================================================================


@dataclass(frozen=True, slots=True)
class EncodingParams:
    """Video encoding parameters (0x20 response).

    Attributes:
        stream_type: Stream type (recording/main/sub).
        enc_type: Encoding type (H.264/H.265).
        resolution_w: Resolution width in pixels.
        resolution_h: Resolution height in pixels.
        bitrate_kbps: Fixed bitrate in kbps.
        frame_rate: Frame rate in fps.

    """

    stream_type: StreamType
    enc_type: VideoEncType
    resolution_w: int
    resolution_h: int
    bitrate_kbps: int
    frame_rate: int


# =============================================================================
# Temperature Measurement
# =============================================================================


@dataclass(frozen=True, slots=True)
class TempPoint:
    """Temperature at a specific point (0x12 response).

    Attributes:
        x: X coordinate of the point.
        y: Y coordinate of the point.
        temperature_c: Temperature in Celsius (raw/100).

    """

    x: int
    y: int
    temperature_c: float


@dataclass(frozen=True, slots=True)
class TempRegion:
    """Temperature measurement in a region (0x13 response).

    Attributes:
        startx: Starting X coordinate of rectangle.
        starty: Starting Y coordinate of rectangle.
        endx: Ending X coordinate of rectangle.
        endy: Ending Y coordinate of rectangle.
        max_c: Maximum temperature in Celsius.
        min_c: Minimum temperature in Celsius.
        max_x: X coordinate of maximum temperature.
        max_y: Y coordinate of maximum temperature.
        min_x: X coordinate of minimum temperature.
        min_y: Y coordinate of minimum temperature.

    """

    startx: int
    starty: int
    endx: int
    endy: int
    max_c: float
    min_c: float
    max_x: int
    max_y: int
    min_x: int
    min_y: int


@dataclass(frozen=True, slots=True)
class TempGlobal:
    """Global temperature measurement (0x14 response).

    Attributes:
        max_c: Maximum temperature in the frame in Celsius.
        min_c: Minimum temperature in the frame in Celsius.
        max_x: X coordinate of maximum temperature.
        max_y: Y coordinate of maximum temperature.
        min_x: X coordinate of minimum temperature.
        min_y: Y coordinate of minimum temperature.

    """

    max_c: float
    min_c: float
    max_x: int
    max_y: int
    min_x: int
    min_y: int


@dataclass(frozen=True, slots=True)
class EnvCorrectionParams:
    """Environmental correction parameters (0x39/0x3A response).

    All values are raw uint16 divided by 100.

    Attributes:
        distance_m: Distance to target in meters.
        emissivity_pct: Target emissivity percentage.
        humidity_pct: Environmental humidity percentage.
        ambient_c: Atmospheric temperature in Celsius.
        reflective_c: Reflective temperature in Celsius.

    """

    distance_m: float
    emissivity_pct: float
    humidity_pct: float
    ambient_c: float
    reflective_c: float


# =============================================================================
# Laser Ranging
# =============================================================================


@dataclass(frozen=True, slots=True)
class LaserDistance:
    """Laser distance measurement (0x15 response).

    Attributes:
        distance_m: Distance in meters, or None if out of range.
            Raw value is in decimeters, divided by 10.
            Returns None if raw < 50 or raw == 0.

    """

    distance_m: float | None


@dataclass(frozen=True, slots=True)
class LaserTargetLatLon:
    """Laser target latitude/longitude (0x17 response).

    Coordinates are in WGS84/EGM96 ellipsoid.

    Attributes:
        lat_e7: Latitude in degrees * 10^7.
        lon_e7: Longitude in degrees * 10^7.

    """

    lat_e7: int
    lon_e7: int


# =============================================================================
# Zoom Control
# =============================================================================


@dataclass(frozen=True, slots=True)
class ZoomRange:
    """Zoom range information (0x16 response).

    Attributes:
        max_int: Integer part of maximum zoom.
        max_float: Decimal part of maximum zoom (0-9).

    """

    max_int: int
    max_float: int

    @property
    def max_zoom(self) -> float:
        """Get the maximum zoom as a float.

        Returns:
            Maximum zoom value (e.g., 30.5 for max_int=30, max_float=5).

        """
        return self.max_int + self.max_float / 10


@dataclass(frozen=True, slots=True)
class CurrentZoom:
    """Current zoom magnification (0x18 response).

    Attributes:
        integer: Integer part of current zoom.
        decimal: Decimal part of current zoom (0-9).

    """

    integer: int
    decimal: int

    @property
    def zoom(self) -> float:
        """Get the current zoom as a float.

        Returns:
            Current zoom value (e.g., 5.3 for integer=5, decimal=3).

        """
        return self.integer + self.decimal / 10


# =============================================================================
# GPS Data
# =============================================================================


@dataclass(frozen=True, slots=True)
class RawGPS:
    """Raw GPS data (0x3E send format).

    Attributes:
        time_boot_ms: Timestamp since system boot in milliseconds.
        lat_e7: Latitude in degrees * 10^7.
        lon_e7: Longitude in degrees * 10^7.
        alt_msl_cm: Altitude MSL in centimeters.
        alt_ellipsoid_cm: Altitude above WGS84 ellipsoid in centimeters.
        vn_mmps: North velocity in mm/s * 10^3 (m E3/s).
        ve_mmps: East velocity in mm/s * 10^3 (m E3/s).
        vd_mmps: Down velocity in mm/s * 10^3 (m E3/s).

    """

    time_boot_ms: int
    lat_e7: int
    lon_e7: int
    alt_msl_cm: int
    alt_ellipsoid_cm: int
    vn_mmps: int
    ve_mmps: int
    vd_mmps: int


# =============================================================================
# System Information
# =============================================================================


@dataclass(frozen=True, slots=True)
class SystemTime:
    """System time (0x40 response).

    Attributes:
        unix_usec: UNIX epoch time in microseconds.
        boot_ms: Time since system startup in milliseconds.

    """

    unix_usec: int
    boot_ms: int


@dataclass(frozen=True, slots=True)
class GimbalSystemInfo:
    """Gimbal system information (0x31 response).

    Attributes:
        laser_state: True if laser ranging is enabled.

    """

    laser_state: bool


# =============================================================================
# IR Threshold Parameters
# =============================================================================


@dataclass(frozen=True, slots=True)
class IRThreshRegion:
    """IR threshold region parameters.

    Attributes:
        switch: Region enable switch (0=hide, 1=display).
        temp_min: Minimum temperature threshold.
        temp_max: Maximum temperature threshold.
        color_r: Red component of region color (0-255).
        color_g: Green component of region color (0-255).
        color_b: Blue component of region color (0-255).

    """

    switch: int
    temp_min: int
    temp_max: int
    color_r: int
    color_g: int
    color_b: int


@dataclass(frozen=True, slots=True)
class IRThreshParams:
    """IR threshold parameters (0x44/0x45 response).

    Contains 3 threshold regions for thermal imaging.

    Attributes:
        region1: First threshold region.
        region2: Second threshold region.
        region3: Third threshold region.

    """

    region1: IRThreshRegion
    region2: IRThreshRegion
    region3: IRThreshRegion


# =============================================================================
# AI Tracking
# =============================================================================


@dataclass(frozen=True, slots=True)
class AITrackingTarget:
    """AI tracking target information (0x50 response).

    Pixel coordinates are based on 1280x720 resolution.

    Attributes:
        x: Target center X coordinate.
        y: Target center Y coordinate.
        w: Target bounding box width.
        h: Target bounding box height.
        target_id: Target type identification.
        status: Tracking status.

    """

    x: int
    y: int
    w: int
    h: int
    target_id: AITargetID
    status: AITrackStatus


# =============================================================================
# Network Configuration
# =============================================================================


@dataclass(frozen=True, slots=True)
class IPConfig:
    """IP configuration (0x81/0x82 response).

    Attributes:
        ip: IP address.
        mask: Subnet mask.
        gateway: Gateway address.

    """

    ip: IPv4Address
    mask: IPv4Address
    gateway: IPv4Address


# =============================================================================
# Angle Limits
# =============================================================================


@dataclass(frozen=True, slots=True)
class AngleLimits:
    """Angle limits for a specific product.

    Attributes:
        yaw_min: Minimum yaw angle in degrees.
        yaw_max: Maximum yaw angle in degrees.
        pitch_min: Minimum pitch angle in degrees.
        pitch_max: Maximum pitch angle in degrees.

    """

    yaw_min: float
    yaw_max: float
    pitch_min: float
    pitch_max: float


# Per-product angle limits table
ANGLE_LIMITS: Final[dict[ProductID, AngleLimits]] = {
    ProductID.ZR10: AngleLimits(yaw_min=-135.0, yaw_max=135.0, pitch_min=-90.0, pitch_max=25.0),
    ProductID.A8_MINI: AngleLimits(yaw_min=-135.0, yaw_max=135.0, pitch_min=-90.0, pitch_max=25.0),
    ProductID.ZR30: AngleLimits(yaw_min=-270.0, yaw_max=270.0, pitch_min=-90.0, pitch_max=25.0),
    ProductID.A2_MINI: AngleLimits(yaw_min=0.0, yaw_max=0.0, pitch_min=-90.0, pitch_max=25.0),
    ProductID.QUAD_SPECTRUM: AngleLimits(
        yaw_min=-360.0, yaw_max=360.0, pitch_min=-90.0, pitch_max=25.0
    ),
}


# =============================================================================
# Media / Web Server Models
# =============================================================================


class MediaType(IntEnum):
    """Media type for the camera web-server file API."""

    IMAGES = 0
    VIDEOS = 1


@dataclass(frozen=True, slots=True)
class MediaDirectory:
    """A directory entry returned by the camera web server.

    Attributes:
        name: Directory display name.
        path: Relative path usable in subsequent API calls.

    """

    name: str
    path: str


@dataclass(frozen=True, slots=True)
class MediaFile:
    """A media file entry returned by the camera web server.

    Attributes:
        name: File name (e.g. "IMG_0001.jpg").
        url: Full URL to download the file directly from the camera.

    """

    name: str
    url: str
