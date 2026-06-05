# Copyright (c) 2026 Mohamed Abdelkader <mohamedashraf123@gmail.com>
# All rights reserved.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

"""Tests for the SIYIClient high-level API."""

from __future__ import annotations

import asyncio
from ipaddress import IPv4Address

import pytest

from siyi_sdk.client import SIYIClient
from siyi_sdk.constants import (
    CMD_CAPTURE_PHOTO_RECORD_VIDEO,
    CMD_REQUEST_FIRMWARE_VERSION,
    CMD_REQUEST_GIMBAL_ATTITUDE,
    CMD_REQUEST_LASER_DISTANCE,
    CMD_SEND_AIRCRAFT_ATTITUDE,
    CMD_SEND_RAW_GPS,
    CMD_SEND_RC_CHANNELS,
)
from siyi_sdk.exceptions import TimeoutError
from siyi_sdk.models import (
    AircraftAttitude,
    AIStreamStatus,
    AITrackingTarget,
    CameraSystemInfo,
    CaptureFuncType,
    CenteringAction,
    ControlMode,
    DataStreamFreq,
    EncodingParams,
    EnvCorrectionParams,
    FCDataType,
    FileNameType,
    FileType,
    FirmwareVersion,
    FunctionFeedback,
    GimbalAttitude,
    GimbalDataType,
    GimbalMotionMode,
    GimbalSystemInfo,
    HardwareID,
    IPConfig,
    IRThreshParams,
    IRThreshPrecision,
    IRThreshRegion,
    LaserDistance,
    LaserTargetLatLon,
    MagneticEncoderAngles,
    MotorVoltage,
    PseudoColor,
    RawGPS,
    RCChannels,
    SetAttitudeAck,
    StreamType,
    SystemTime,
    TempGlobal,
    TempMeasureFlag,
    TempPoint,
    TempRegion,
    ThermalGain,
    ThermalOutputMode,
    VideoEncType,
    VideoStitchingMode,
    WeakControlThreshold,
    ZoomRange,
)
from siyi_sdk.protocol.frame import Frame
from siyi_sdk.transport.mock import MockTransport


@pytest.fixture
def mock_transport() -> MockTransport:
    """Create a mock transport for testing."""
    return MockTransport(supports_heartbeat=False)


@pytest.fixture
def mock_transport_tcp() -> MockTransport:
    """Create a mock transport simulating TCP with heartbeat support."""
    return MockTransport(supports_heartbeat=True)


class TestClientLifecycle:
    """Test client lifecycle management."""

    @pytest.mark.asyncio
    async def test_context_manager(self, mock_transport: MockTransport) -> None:
        """Test async context manager usage."""
        async with SIYIClient(mock_transport) as client:
            assert mock_transport.is_connected
            assert client._reader_task is not None

        # After exit, transport should be closed
        assert not mock_transport.is_connected

    @pytest.mark.asyncio
    async def test_manual_connect_close(self, mock_transport: MockTransport) -> None:
        """Test manual connect/close lifecycle."""
        client = SIYIClient(mock_transport)
        assert not mock_transport.is_connected

        await client.connect()
        assert mock_transport.is_connected

        await client.close()
        assert not mock_transport.is_connected

    @pytest.mark.asyncio
    async def test_heartbeat_started_for_tcp(self, mock_transport_tcp: MockTransport) -> None:
        """Test heartbeat task is started for TCP transports."""
        client = SIYIClient(mock_transport_tcp)
        await client.connect()

        assert client._heartbeat_task is not None
        assert not client._heartbeat_task.done()

        await client.close()

    @pytest.mark.asyncio
    async def test_heartbeat_not_started_for_udp(self, mock_transport: MockTransport) -> None:
        """Test heartbeat task is not started for UDP transports."""
        client = SIYIClient(mock_transport)
        await client.connect()

        assert client._heartbeat_task is None

        await client.close()

    @pytest.mark.asyncio
    async def test_heartbeat_sends_frames(self, mock_transport_tcp: MockTransport) -> None:
        """Test heartbeat task sends 3 frames in 3.1 seconds."""
        client = SIYIClient(mock_transport_tcp)
        await client.connect()

        # Wait for 3.1 seconds
        await asyncio.sleep(3.1)

        await client.close()

        # Check sent frames for heartbeat frames
        heartbeat_count = sum(
            1 for frame in mock_transport_tcp.sent_frames if frame.hex() == "556601010000000000598b"
        )
        assert heartbeat_count == 3

    @pytest.mark.asyncio
    async def test_no_heartbeat_for_udp(self, mock_transport: MockTransport) -> None:
        """Test no heartbeat frames for UDP transport."""
        client = SIYIClient(mock_transport)
        await client.connect()

        await asyncio.sleep(3.1)

        await client.close()

        # No heartbeat frames should be sent
        heartbeat_count = sum(
            1 for frame in mock_transport.sent_frames if frame.hex() == "556601010000000000598b"
        )
        assert heartbeat_count == 0


class TestSequenceNumber:
    """Test sequence number generation."""

    @pytest.mark.asyncio
    async def test_seq_increment(self, mock_transport: MockTransport) -> None:
        """Test sequence numbers increment correctly."""
        client = SIYIClient(mock_transport)

        seq1 = client._next_seq()
        seq2 = client._next_seq()
        seq3 = client._next_seq()

        assert seq1 == 0
        assert seq2 == 1
        assert seq3 == 2

    @pytest.mark.asyncio
    async def test_seq_wrap(self, mock_transport: MockTransport) -> None:
        """Test sequence number wraps at 0xFFFF."""
        client = SIYIClient(mock_transport)
        client._seq = 0xFFFE

        seq1 = client._next_seq()
        seq2 = client._next_seq()
        seq3 = client._next_seq()

        assert seq1 == 0xFFFE
        assert seq2 == 0xFFFF
        assert seq3 == 0x0000

    @pytest.mark.asyncio
    async def test_seq_uniqueness_70k(self, mock_transport: MockTransport) -> None:
        """Test 70,000 sequence numbers cover all 16-bit values."""
        client = SIYIClient(mock_transport)

        seqs = [client._next_seq() for _ in range(70000)]

        # All 16-bit values should be produced
        unique_seqs = {s & 0xFFFF for s in seqs}
        assert len(unique_seqs) == 65536


class TestCommandExecution:
    """Test command execution and timeout handling."""

    @pytest.mark.asyncio
    async def test_get_firmware_version(self, mock_transport: MockTransport) -> None:
        """Test get_firmware_version happy path."""
        client = SIYIClient(mock_transport)
        await client.connect()

        # Queue ACK response
        ack_payload = b"\x03\x02\x02\x6e\x03\x02\x02\x6e\x01\x01\x01\x63"
        ack_frame = Frame.build(CMD_REQUEST_FIRMWARE_VERSION, ack_payload, seq=0, need_ack=False)
        mock_transport.queue_response(ack_frame.to_bytes())

        version = await client.get_firmware_version()

        assert isinstance(version, FirmwareVersion)
        assert version.camera == 0x6E020203
        assert version.gimbal == 0x6E020203

        await client.close()

    @pytest.mark.asyncio
    async def test_timeout_raises_error(self, mock_transport: MockTransport) -> None:
        """Test timeout raises TimeoutError."""
        client = SIYIClient(mock_transport, default_timeout=0.1)
        await client.connect()

        # Do not queue a response
        with pytest.raises(TimeoutError) as exc_info:
            await client.get_firmware_version()

        err = exc_info.value
        assert err.cmd_id == CMD_REQUEST_FIRMWARE_VERSION
        assert err.timeout_s == 0.1

        await client.close()

    @pytest.mark.asyncio
    async def test_retry_on_idempotent_read(self, mock_transport: MockTransport) -> None:
        """Test idempotent reads retry on timeout."""
        client = SIYIClient(mock_transport, default_timeout=0.1, max_retries=1)
        await client.connect()

        # Queue response after both attempts would have been sent
        async def delayed_response() -> None:
            await asyncio.sleep(
                0.25
            )  # Wait for first timeout + retry delay + part of second attempt
            ack_payload = b"\x03\x02\x02\x6e\x03\x02\x02\x6e\x01\x01\x01\x63"
            ack_frame = Frame.build(
                CMD_REQUEST_FIRMWARE_VERSION, ack_payload, seq=0, need_ack=False
            )
            mock_transport.queue_response(ack_frame.to_bytes())

        task = asyncio.create_task(delayed_response())

        version = await client.get_firmware_version()
        await task
        assert isinstance(version, FirmwareVersion)

        await client.close()

    @pytest.mark.asyncio
    async def test_no_retry_on_write(self, mock_transport: MockTransport) -> None:
        """Test write commands do not retry on timeout."""
        client = SIYIClient(mock_transport, default_timeout=0.1, max_retries=1)
        await client.connect()

        # Do not queue response
        with pytest.raises(TimeoutError):
            await client.set_pseudo_color(PseudoColor.WHITE_HOT)

        await client.close()

    @pytest.mark.asyncio
    async def test_concurrent_same_cmd_id(self, mock_transport: MockTransport) -> None:
        """Test concurrent requests with same CMD_ID are serialized."""
        client = SIYIClient(mock_transport)
        await client.connect()

        # Queue responses with a delay to ensure requests are sent first
        async def queue_responses() -> None:
            await asyncio.sleep(0.05)
            ack_payload1 = b"\x03\x02\x02\x6e\x03\x02\x02\x6e\x01\x01\x01\x63"
            ack_frame1 = Frame.build(
                CMD_REQUEST_FIRMWARE_VERSION, ack_payload1, seq=0, need_ack=False
            )
            mock_transport.queue_response(ack_frame1.to_bytes())

            await asyncio.sleep(0.05)
            ack_payload2 = b"\x04\x03\x03\x6f\x04\x03\x03\x6f\x02\x02\x02\x64"
            ack_frame2 = Frame.build(
                CMD_REQUEST_FIRMWARE_VERSION, ack_payload2, seq=1, need_ack=False
            )
            mock_transport.queue_response(ack_frame2.to_bytes())

        task = asyncio.create_task(queue_responses())

        # Execute concurrently
        results = await asyncio.gather(client.get_firmware_version(), client.get_firmware_version())
        await task

        # Both should succeed
        assert len(results) == 2
        assert all(isinstance(r, FirmwareVersion) for r in results)

        # Check sent frames (should be 2)
        assert len(mock_transport.sent_frames) == 2

        await client.close()

    @pytest.mark.asyncio
    async def test_concurrent_different_cmd_id(self, mock_transport: MockTransport) -> None:
        """Test concurrent requests with different CMD_IDs execute in parallel."""
        client = SIYIClient(mock_transport)
        await client.connect()

        # Queue responses with a delay
        async def queue_responses() -> None:
            await asyncio.sleep(0.05)
            firmware_ack = b"\x03\x02\x02\x6e\x03\x02\x02\x6e\x01\x01\x01\x63"
            firmware_frame = Frame.build(
                CMD_REQUEST_FIRMWARE_VERSION, firmware_ack, seq=0, need_ack=False
            )
            mock_transport.queue_response(firmware_frame.to_bytes())

            attitude_ack = b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
            attitude_frame = Frame.build(
                CMD_REQUEST_GIMBAL_ATTITUDE, attitude_ack, seq=1, need_ack=False
            )
            mock_transport.queue_response(attitude_frame.to_bytes())

        response_task = asyncio.create_task(queue_responses())

        # Execute concurrently
        firmware_task = asyncio.create_task(client.get_firmware_version())
        attitude_task = asyncio.create_task(client.get_gimbal_attitude())

        firmware, attitude = await asyncio.gather(firmware_task, attitude_task)
        await response_task

        assert isinstance(firmware, FirmwareVersion)
        assert isinstance(attitude, GimbalAttitude)

        await client.close()

    @pytest.mark.asyncio
    async def test_fire_and_forget_capture(self, mock_transport: MockTransport) -> None:
        """Test fire-and-forget commands do not wait for ACK."""
        client = SIYIClient(mock_transport)
        await client.connect()

        # Do not queue response
        await client.capture(CaptureFuncType.PHOTO)

        # Should return immediately
        assert len(mock_transport.sent_frames) == 1
        sent_frame = Frame.from_bytes(mock_transport.sent_frames[0])
        assert sent_frame.cmd_id == CMD_CAPTURE_PHOTO_RECORD_VIDEO

        await client.close()

    @pytest.mark.asyncio
    async def test_fire_and_forget_send_aircraft_attitude(
        self, mock_transport: MockTransport
    ) -> None:
        """Test send_aircraft_attitude is fire-and-forget."""
        client = SIYIClient(mock_transport)
        await client.connect()

        att = AircraftAttitude(
            time_boot_ms=1000,
            roll_rad=0.1,
            pitch_rad=0.2,
            yaw_rad=0.3,
            rollspeed=0.01,
            pitchspeed=0.02,
            yawspeed=0.03,
        )

        await client.send_aircraft_attitude(att)

        sent_frame = Frame.from_bytes(mock_transport.sent_frames[0])
        assert sent_frame.cmd_id == CMD_SEND_AIRCRAFT_ATTITUDE

        await client.close()

    @pytest.mark.asyncio
    async def test_fire_and_forget_send_rc_channels(self, mock_transport: MockTransport) -> None:
        """Test send_rc_channels is fire-and-forget."""
        client = SIYIClient(mock_transport)
        await client.connect()

        ch = RCChannels(chans=tuple([1500] * 18), chancount=16, rssi=200)

        with pytest.warns(DeprecationWarning):
            await client.send_rc_channels(ch)

        sent_frame = Frame.from_bytes(mock_transport.sent_frames[0])
        assert sent_frame.cmd_id == CMD_SEND_RC_CHANNELS

        await client.close()

    @pytest.mark.asyncio
    async def test_fire_and_forget_send_raw_gps(self, mock_transport: MockTransport) -> None:
        """Test send_raw_gps is fire-and-forget."""
        client = SIYIClient(mock_transport)
        await client.connect()

        gps = RawGPS(
            time_boot_ms=2000,
            lat_e7=123456789,
            lon_e7=987654321,
            alt_msl_cm=100000,
            alt_ellipsoid_cm=100500,
            vn_mmps=1000,
            ve_mmps=2000,
            vd_mmps=500,
        )

        await client.send_raw_gps(gps)

        sent_frame = Frame.from_bytes(mock_transport.sent_frames[0])
        assert sent_frame.cmd_id == CMD_SEND_RAW_GPS

        await client.close()


class TestStreamSubscriptions:
    """Test stream subscription API."""

    @pytest.mark.asyncio
    async def test_on_attitude_subscription(self, mock_transport: MockTransport) -> None:
        """Test attitude stream subscription."""
        client = SIYIClient(mock_transport)
        await client.connect()

        received: list[GimbalAttitude] = []

        def callback(att: GimbalAttitude) -> None:
            received.append(att)

        unsub = client.on_attitude(callback)

        # Queue 5 attitude push frames
        for i in range(5):
            payload = b"\x00\x00" * 6  # 12 bytes of zeros
            frame = Frame.build(CMD_REQUEST_GIMBAL_ATTITUDE, payload, seq=i, need_ack=False)
            mock_transport.queue_response(frame.to_bytes())

        # Allow reader to process
        await asyncio.sleep(0.2)

        assert len(received) == 5

        # Unsubscribe
        unsub()

        # Queue another frame
        frame = Frame.build(CMD_REQUEST_GIMBAL_ATTITUDE, b"\x00\x00" * 6, seq=10, need_ack=False)
        mock_transport.queue_response(frame.to_bytes())

        await asyncio.sleep(0.2)

        # Should still be 5 (no new callbacks)
        assert len(received) == 5

        await client.close()

    @pytest.mark.asyncio
    async def test_on_laser_distance_subscription(self, mock_transport: MockTransport) -> None:
        """Test laser distance stream subscription."""
        client = SIYIClient(mock_transport)
        await client.connect()

        received: list[LaserDistance] = []

        def callback(laser: LaserDistance) -> None:
            received.append(laser)

        unsub = client.on_laser_distance(callback)

        # Queue 3 laser push frames (raw value 1000 = 100.0 m)
        for i in range(3):
            payload = b"\xe8\x03"  # 1000 in little-endian
            frame = Frame.build(CMD_REQUEST_LASER_DISTANCE, payload, seq=i, need_ack=False)
            mock_transport.queue_response(frame.to_bytes())

        await asyncio.sleep(0.2)

        assert len(received) == 3
        assert all(ld.distance_m == 100.0 for ld in received)

        unsub()
        await client.close()

    @pytest.mark.asyncio
    async def test_on_function_feedback_subscription(self, mock_transport: MockTransport) -> None:
        """Test function feedback stream subscription."""
        client = SIYIClient(mock_transport)
        await client.connect()

        received: list[FunctionFeedback] = []

        def callback(fb: FunctionFeedback) -> None:
            received.append(fb)

        unsub = client.on_function_feedback(callback)

        # Queue 2 function feedback frames
        for i in range(2):
            payload = b"\x00"  # PHOTO_OK
            frame = Frame.build(0x0B, payload, seq=i, need_ack=False)
            mock_transport.queue_response(frame.to_bytes())

        await asyncio.sleep(0.2)

        assert len(received) == 2
        assert all(fb == FunctionFeedback.PHOTO_OK for fb in received)

        unsub()
        await client.close()

    @pytest.mark.asyncio
    async def test_on_ai_tracking_subscription(self, mock_transport: MockTransport) -> None:
        """Test AI tracking stream subscription."""
        client = SIYIClient(mock_transport)
        await client.connect()

        received: list[AITrackingTarget] = []

        def callback(target: AITrackingTarget) -> None:
            received.append(target)

        unsub = client.on_ai_tracking(callback)

        # Queue 2 AI tracking frames
        for i in range(2):
            payload = b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"  # 10 bytes
            frame = Frame.build(0x50, payload, seq=i, need_ack=False)
            mock_transport.queue_response(frame.to_bytes())

        await asyncio.sleep(0.2)

        assert len(received) == 2

        unsub()
        await client.close()


class TestUnexpectedFrames:
    """Test handling of unexpected frames."""

    @pytest.mark.asyncio
    async def test_unknown_cmd_id_logged(
        self, mock_transport: MockTransport, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test unknown CMD_ID is logged as warning."""
        client = SIYIClient(mock_transport)
        await client.connect()

        # Queue a frame with unknown CMD_ID
        frame = Frame.build(0x03, b"", seq=0, need_ack=False)
        mock_transport.queue_response(frame.to_bytes())

        await asyncio.sleep(0.2)

        # Check stdout (structlog outputs to stdout by default)
        captured = capsys.readouterr()
        assert "unexpected_frame" in captured.out or "0x03" in captured.out

        await client.close()


class TestSystemCommands:
    """Test all system command methods."""

    @pytest.mark.asyncio
    async def test_get_hardware_id(self, mock_transport: MockTransport) -> None:
        """Test get_hardware_id."""
        client = SIYIClient(mock_transport)
        await client.connect()

        # Queue ACK
        ack_payload = b"\x73" + b"\x00" * 11  # A8_MINI product ID
        ack_frame = Frame.build(0x02, ack_payload, seq=0, need_ack=False)
        mock_transport.queue_response(ack_frame.to_bytes())

        hw_id = await client.get_hardware_id()

        assert isinstance(hw_id, HardwareID)
        assert hw_id.raw[0] == 0x73

        await client.close()

    @pytest.mark.asyncio
    async def test_get_system_time(self, mock_transport: MockTransport) -> None:
        """Test get_system_time."""
        client = SIYIClient(mock_transport)
        await client.connect()

        # Queue ACK
        ack_payload = b"\x00" * 8 + b"\x00" * 4  # 12 bytes
        ack_frame = Frame.build(0x40, ack_payload, seq=0, need_ack=False)
        mock_transport.queue_response(ack_frame.to_bytes())

        sys_time = await client.get_system_time()

        assert isinstance(sys_time, SystemTime)

        await client.close()

    @pytest.mark.asyncio
    async def test_set_utc_time(self, mock_transport: MockTransport) -> None:
        """Test set_utc_time."""
        client = SIYIClient(mock_transport)
        await client.connect()

        # Queue ACK
        ack_payload = b"\x01"  # Success
        ack_frame = Frame.build(0x30, ack_payload, seq=0, need_ack=False)
        mock_transport.queue_response(ack_frame.to_bytes())

        result = await client.set_utc_time(1234567890123456)

        assert result is True

        await client.close()

    @pytest.mark.asyncio
    async def test_get_gimbal_system_info(self, mock_transport: MockTransport) -> None:
        """Test get_gimbal_system_info."""
        client = SIYIClient(mock_transport)
        await client.connect()

        # Queue ACK
        ack_payload = b"\x00"  # Laser off
        ack_frame = Frame.build(0x31, ack_payload, seq=0, need_ack=False)
        mock_transport.queue_response(ack_frame.to_bytes())

        info = await client.get_gimbal_system_info()

        assert isinstance(info, GimbalSystemInfo)
        assert info.laser_state is False

        await client.close()

    @pytest.mark.asyncio
    async def test_soft_reboot(self, mock_transport: MockTransport) -> None:
        """Test soft_reboot."""
        client = SIYIClient(mock_transport)
        await client.connect()

        # Queue ACK
        ack_payload = b"\x01\x01"  # Both rebooted
        ack_frame = Frame.build(0x80, ack_payload, seq=0, need_ack=False)
        mock_transport.queue_response(ack_frame.to_bytes())

        camera, gimbal = await client.soft_reboot(camera=True, gimbal=True)

        assert camera is True
        assert gimbal is True

        await client.close()

    @pytest.mark.asyncio
    async def test_get_ip_config(self, mock_transport: MockTransport) -> None:
        """Test get_ip_config."""
        client = SIYIClient(mock_transport)
        await client.connect()

        # Queue ACK (12 bytes: 3x IPv4 addresses as little-endian uint32)
        # 192.168.144.25 = 0xC0A89019 → little-endian bytes: 0x19 0x90 0xA8 0xC0
        ack_payload = (
            b"\x19\x90\xa8\xc0"  # 192.168.144.25
            + b"\x00\xff\xff\xff"  # 255.255.255.0
            + b"\x01\x90\xa8\xc0"  # 192.168.144.1
        )
        ack_frame = Frame.build(0x81, ack_payload, seq=0, need_ack=False)
        mock_transport.queue_response(ack_frame.to_bytes())

        config = await client.get_ip_config()

        assert isinstance(config, IPConfig)
        assert config.ip == IPv4Address("192.168.144.25")
        assert config.mask == IPv4Address("255.255.255.0")
        assert config.gateway == IPv4Address("192.168.144.1")

        await client.close()

    @pytest.mark.asyncio
    async def test_set_ip_config(self, mock_transport: MockTransport) -> None:
        """Test set_ip_config."""
        client = SIYIClient(mock_transport)
        await client.connect()

        # Queue ACK
        ack_payload = b"\x01"  # Success
        ack_frame = Frame.build(0x82, ack_payload, seq=0, need_ack=False)
        mock_transport.queue_response(ack_frame.to_bytes())

        config = IPConfig(
            ip=IPv4Address("192.168.144.30"),
            mask=IPv4Address("255.255.255.0"),
            gateway=IPv4Address("192.168.144.1"),
        )

        await client.set_ip_config(config)

        await client.close()


class TestFocusZoomCommands:
    """Test focus and zoom commands."""

    @pytest.mark.asyncio
    async def test_auto_focus(self, mock_transport: MockTransport) -> None:
        """Test auto_focus."""
        client = SIYIClient(mock_transport)
        await client.connect()

        # Queue ACK
        ack_payload = b"\x01"  # Success
        ack_frame = Frame.build(0x04, ack_payload, seq=0, need_ack=False)
        mock_transport.queue_response(ack_frame.to_bytes())

        await client.auto_focus(50, 50)

        await client.close()

    @pytest.mark.asyncio
    async def test_manual_zoom(self, mock_transport: MockTransport) -> None:
        """Test manual_zoom."""
        client = SIYIClient(mock_transport)
        await client.connect()

        # Queue ACK (2 bytes: zoom = 5.3x)
        ack_payload = b"\x35\x00"  # 53 in little-endian
        ack_frame = Frame.build(0x05, ack_payload, seq=0, need_ack=False)
        mock_transport.queue_response(ack_frame.to_bytes())

        zoom = await client.manual_zoom(1)

        assert zoom == 5.3

        await client.close()

    @pytest.mark.asyncio
    async def test_manual_focus(self, mock_transport: MockTransport) -> None:
        """Test manual_focus."""
        client = SIYIClient(mock_transport)
        await client.connect()

        # Queue ACK
        ack_payload = b"\x01"
        ack_frame = Frame.build(0x06, ack_payload, seq=0, need_ack=False)
        mock_transport.queue_response(ack_frame.to_bytes())

        await client.manual_focus(1)

        await client.close()

    @pytest.mark.asyncio
    async def test_absolute_zoom(self, mock_transport: MockTransport) -> None:
        """Test absolute_zoom."""
        client = SIYIClient(mock_transport)
        await client.connect()

        # Queue ACK
        ack_payload = b"\x01"
        ack_frame = Frame.build(0x0F, ack_payload, seq=0, need_ack=False)
        mock_transport.queue_response(ack_frame.to_bytes())

        await client.absolute_zoom(10.5)

        await client.close()

    @pytest.mark.asyncio
    async def test_get_zoom_range(self, mock_transport: MockTransport) -> None:
        """Test get_zoom_range."""
        client = SIYIClient(mock_transport)
        await client.connect()

        # Queue ACK (2 bytes: max = 30.5x)
        ack_payload = b"\x1e\x05"  # int=30, float=5
        ack_frame = Frame.build(0x16, ack_payload, seq=0, need_ack=False)
        mock_transport.queue_response(ack_frame.to_bytes())

        zoom_range = await client.get_zoom_range()

        assert isinstance(zoom_range, ZoomRange)
        assert zoom_range.max_zoom == 30.5

        await client.close()

    @pytest.mark.asyncio
    async def test_get_current_zoom(self, mock_transport: MockTransport) -> None:
        """Test get_current_zoom."""
        client = SIYIClient(mock_transport)
        await client.connect()

        # Queue ACK (2 bytes: zoom = 8.2x)
        ack_payload = b"\x08\x02"  # int=8, dec=2
        ack_frame = Frame.build(0x18, ack_payload, seq=0, need_ack=False)
        mock_transport.queue_response(ack_frame.to_bytes())

        zoom = await client.get_current_zoom()

        assert zoom == 8.2

        await client.close()


class TestGimbalCommands:
    """Test gimbal control commands."""

    @pytest.mark.asyncio
    async def test_rotate(self, mock_transport: MockTransport) -> None:
        """Test rotate."""
        client = SIYIClient(mock_transport)
        await client.connect()

        # Queue ACK
        ack_payload = b"\x01"
        ack_frame = Frame.build(0x07, ack_payload, seq=0, need_ack=False)
        mock_transport.queue_response(ack_frame.to_bytes())

        await client.rotate(10, -20)

        await client.close()

    @pytest.mark.asyncio
    async def test_one_key_centering(self, mock_transport: MockTransport) -> None:
        """Test one_key_centering."""
        client = SIYIClient(mock_transport)
        await client.connect()

        # Queue ACK
        ack_payload = b"\x01"
        ack_frame = Frame.build(0x08, ack_payload, seq=0, need_ack=False)
        mock_transport.queue_response(ack_frame.to_bytes())

        await client.one_key_centering(CenteringAction.CENTER)

        await client.close()

    @pytest.mark.asyncio
    async def test_set_attitude(self, mock_transport: MockTransport) -> None:
        """Test set_attitude."""
        client = SIYIClient(mock_transport)
        await client.connect()

        # Queue ACK (6 bytes: yaw, pitch, roll each int16)
        ack_payload = b"\x00\x00\x00\x00\x00\x00"
        ack_frame = Frame.build(0x0E, ack_payload, seq=0, need_ack=False)
        mock_transport.queue_response(ack_frame.to_bytes())

        ack = await client.set_attitude(45.0, -30.0)

        assert isinstance(ack, SetAttitudeAck)

        await client.close()

    @pytest.mark.asyncio
    async def test_set_single_axis(self, mock_transport: MockTransport) -> None:
        """Test set_single_axis."""
        client = SIYIClient(mock_transport)
        await client.connect()

        # Queue ACK (6 bytes)
        ack_payload = b"\x00\x00\x00\x00\x00\x00"
        ack_frame = Frame.build(0x41, ack_payload, seq=0, need_ack=False)
        mock_transport.queue_response(ack_frame.to_bytes())

        ack = await client.set_single_axis("yaw", 90.0)

        assert isinstance(ack, SetAttitudeAck)

        await client.close()

    @pytest.mark.asyncio
    async def test_rotate_nowait(self, mock_transport: MockTransport) -> None:
        """rotate_nowait sends a 0x07 frame with CTRL=0 and does not wait for ACK."""
        client = SIYIClient(mock_transport)
        await client.connect()

        # Note: no queue_response — fire-and-forget must not block.
        await client.rotate_nowait(50, -25)

        assert len(mock_transport.sent_frames) == 1
        sent = Frame.from_bytes(mock_transport.sent_frames[0])
        assert sent.cmd_id == 0x07
        assert sent.ctrl == 0  # need_ack must be cleared
        # Payload: 2 x int8 little-endian.
        assert sent.data == b"\x32\xe7"  # 50, -25

        await client.close()

    @pytest.mark.asyncio
    async def test_rotate_nowait_range_validation(
        self, mock_transport: MockTransport
    ) -> None:
        """rotate_nowait still validates the -100..100 range."""
        from siyi_sdk.exceptions import ConfigurationError

        client = SIYIClient(mock_transport)
        await client.connect()

        with pytest.raises(ConfigurationError):
            await client.rotate_nowait(150, 0)
        with pytest.raises(ConfigurationError):
            await client.rotate_nowait(0, -200)

        # Failed encodes must not have been transmitted.
        assert len(mock_transport.sent_frames) == 0

        await client.close()

    @pytest.mark.asyncio
    async def test_rotate_nowait_high_rate_throughput(
        self, mock_transport: MockTransport
    ) -> None:
        """Many back-to-back fire-and-forget rotates must not deadlock.

        The standard rotate() serialises on a per-CMD_ID lock waiting for
        ACKs; rotate_nowait() must bypass that and accept a burst.
        """
        client = SIYIClient(mock_transport)
        await client.connect()

        for i in range(200):
            await client.rotate_nowait(i % 100, -(i % 100))

        assert len(mock_transport.sent_frames) == 200
        # Every frame must have CTRL=0.
        for raw in mock_transport.sent_frames:
            assert Frame.from_bytes(raw).ctrl == 0

        await client.close()

    @pytest.mark.asyncio
    async def test_set_attitude_nowait(self, mock_transport: MockTransport) -> None:
        """set_attitude_nowait sends a 0x0E frame with CTRL=0."""
        client = SIYIClient(mock_transport)
        await client.connect()

        await client.set_attitude_nowait(45.0, -30.0)

        assert len(mock_transport.sent_frames) == 1
        sent = Frame.from_bytes(mock_transport.sent_frames[0])
        assert sent.cmd_id == 0x0E
        assert sent.ctrl == 0
        # 4-byte payload, int16 little-endian, angles * 10.
        assert sent.data == b"\xc2\x01\xd4\xfe"  # 450, -300

        await client.close()

    @pytest.mark.asyncio
    async def test_set_single_axis_nowait_yaw(
        self, mock_transport: MockTransport
    ) -> None:
        """set_single_axis_nowait('yaw', ...) sends 0x41 with axis byte = 0."""
        client = SIYIClient(mock_transport)
        await client.connect()

        await client.set_single_axis_nowait("yaw", 90.0)

        sent = Frame.from_bytes(mock_transport.sent_frames[0])
        assert sent.cmd_id == 0x41
        assert sent.ctrl == 0

        await client.close()

    @pytest.mark.asyncio
    async def test_set_single_axis_nowait_pitch(
        self, mock_transport: MockTransport
    ) -> None:
        """set_single_axis_nowait('pitch', ...) sends 0x41 with axis byte = 1."""
        client = SIYIClient(mock_transport)
        await client.connect()

        await client.set_single_axis_nowait("pitch", -45.0)

        sent = Frame.from_bytes(mock_transport.sent_frames[0])
        assert sent.cmd_id == 0x41
        assert sent.ctrl == 0

        await client.close()

    @pytest.mark.asyncio
    async def test_get_gimbal_mode(self, mock_transport: MockTransport) -> None:
        """Test get_gimbal_mode."""
        client = SIYIClient(mock_transport)
        await client.connect()

        # Queue ACK (1 byte: mode = LOCK)
        ack_payload = b"\x00"
        ack_frame = Frame.build(0x19, ack_payload, seq=0, need_ack=False)
        mock_transport.queue_response(ack_frame.to_bytes())

        mode = await client.get_gimbal_mode()

        assert mode == GimbalMotionMode.LOCK

        await client.close()


class TestAttitudeStreamCommands:
    """Test attitude and stream commands."""

    @pytest.mark.asyncio
    async def test_get_gimbal_attitude(self, mock_transport: MockTransport) -> None:
        """Test get_gimbal_attitude."""
        client = SIYIClient(mock_transport)
        await client.connect()

        # Queue ACK (12 bytes)
        ack_payload = b"\x00\x00" * 6
        ack_frame = Frame.build(CMD_REQUEST_GIMBAL_ATTITUDE, ack_payload, seq=0, need_ack=False)
        mock_transport.queue_response(ack_frame.to_bytes())

        attitude = await client.get_gimbal_attitude()

        assert isinstance(attitude, GimbalAttitude)

        await client.close()

    @pytest.mark.asyncio
    async def test_request_fc_stream(self, mock_transport: MockTransport) -> None:
        """Test request_fc_stream."""
        client = SIYIClient(mock_transport)
        await client.connect()

        # Queue ACK
        ack_payload = b"\x01"
        ack_frame = Frame.build(0x24, ack_payload, seq=0, need_ack=False)
        mock_transport.queue_response(ack_frame.to_bytes())

        await client.request_fc_stream(FCDataType.ATTITUDE, DataStreamFreq.HZ10)

        # Check active streams
        assert FCDataType.ATTITUDE in client._active_streams

        await client.close()

    @pytest.mark.asyncio
    async def test_request_gimbal_stream(self, mock_transport: MockTransport) -> None:
        """Test request_gimbal_stream."""
        client = SIYIClient(mock_transport)
        await client.connect()

        # Queue ACK
        ack_payload = b"\x01"
        ack_frame = Frame.build(0x25, ack_payload, seq=0, need_ack=False)
        mock_transport.queue_response(ack_frame.to_bytes())

        await client.request_gimbal_stream(GimbalDataType.ATTITUDE, DataStreamFreq.HZ5)

        # Check active streams
        assert GimbalDataType.ATTITUDE in client._active_streams

        await client.close()

    @pytest.mark.asyncio
    async def test_get_magnetic_encoder(self, mock_transport: MockTransport) -> None:
        """Test get_magnetic_encoder."""
        client = SIYIClient(mock_transport)
        await client.connect()

        # Queue ACK (6 bytes)
        ack_payload = b"\x00\x00\x00\x00\x00\x00"
        ack_frame = Frame.build(0x26, ack_payload, seq=0, need_ack=False)
        mock_transport.queue_response(ack_frame.to_bytes())

        encoder = await client.get_magnetic_encoder()

        assert isinstance(encoder, MagneticEncoderAngles)

        await client.close()


class TestCameraCommands:
    """Test camera commands."""

    @pytest.mark.asyncio
    async def test_get_camera_system_info(self, mock_transport: MockTransport) -> None:
        """Test get_camera_system_info."""
        client = SIYIClient(mock_transport)
        await client.connect()

        # Queue ACK (8 bytes)
        ack_payload = b"\x00" * 8
        ack_frame = Frame.build(0x0A, ack_payload, seq=0, need_ack=False)
        mock_transport.queue_response(ack_frame.to_bytes())

        info = await client.get_camera_system_info()

        assert isinstance(info, CameraSystemInfo)

        await client.close()

    @pytest.mark.asyncio
    async def test_get_encoding_params(self, mock_transport: MockTransport) -> None:
        """Test get_encoding_params."""
        client = SIYIClient(mock_transport)
        await client.connect()

        # Queue ACK (11 bytes)
        ack_payload = b"\x01\x01\x00\x05\x00\x04\x00\x00\x80\x00\x1e"
        ack_frame = Frame.build(0x20, ack_payload, seq=0, need_ack=False)
        mock_transport.queue_response(ack_frame.to_bytes())

        params = await client.get_encoding_params(StreamType.MAIN)

        assert isinstance(params, EncodingParams)

        await client.close()

    @pytest.mark.asyncio
    async def test_set_encoding_params(self, mock_transport: MockTransport) -> None:
        """Test set_encoding_params."""
        client = SIYIClient(mock_transport)
        await client.connect()

        # Queue ACK (2 bytes: sta, enc_type)
        ack_payload = b"\x01\x02"
        ack_frame = Frame.build(0x21, ack_payload, seq=0, need_ack=False)
        mock_transport.queue_response(ack_frame.to_bytes())

        params = EncodingParams(
            stream_type=StreamType.MAIN,
            enc_type=VideoEncType.H265,
            resolution_w=1920,
            resolution_h=1080,
            bitrate_kbps=4000,
            frame_rate=30,
        )

        result = await client.set_encoding_params(params)

        assert result is True

        await client.close()

    @pytest.mark.asyncio
    async def test_format_sd_card(self, mock_transport: MockTransport) -> None:
        """Test format_sd_card."""
        client = SIYIClient(mock_transport)
        await client.connect()

        # Queue ACK
        ack_payload = b"\x01"
        ack_frame = Frame.build(0x48, ack_payload, seq=0, need_ack=False)
        mock_transport.queue_response(ack_frame.to_bytes())

        result = await client.format_sd_card()

        assert result is True

        await client.close()

    @pytest.mark.asyncio
    async def test_get_picture_name_type(self, mock_transport: MockTransport) -> None:
        """Test get_picture_name_type."""
        client = SIYIClient(mock_transport)
        await client.connect()

        # Queue ACK (2 bytes: file_type, file_name_type)
        ack_payload = b"\x00\x01"  # PICTURE, INDEX
        ack_frame = Frame.build(0x49, ack_payload, seq=0, need_ack=False)
        mock_transport.queue_response(ack_frame.to_bytes())

        name_type = await client.get_picture_name_type(FileType.PICTURE)

        assert name_type == FileNameType.INDEX

        await client.close()

    @pytest.mark.asyncio
    async def test_set_picture_name_type(self, mock_transport: MockTransport) -> None:
        """Test set_picture_name_type."""
        client = SIYIClient(mock_transport)
        await client.connect()

        # Queue ACK (2 bytes: sta, file_name_type)
        ack_payload = b"\x01\x02"
        ack_frame = Frame.build(0x4A, ack_payload, seq=0, need_ack=False)
        mock_transport.queue_response(ack_frame.to_bytes())

        await client.set_picture_name_type(FileType.PICTURE, FileNameType.TIMESTAMP)

        await client.close()

    @pytest.mark.asyncio
    async def test_get_osd_flag(self, mock_transport: MockTransport) -> None:
        """Test get_osd_flag."""
        client = SIYIClient(mock_transport)
        await client.connect()

        # Queue ACK
        ack_payload = b"\x01"  # On
        ack_frame = Frame.build(0x4B, ack_payload, seq=0, need_ack=False)
        mock_transport.queue_response(ack_frame.to_bytes())

        flag = await client.get_osd_flag()

        assert flag is True

        await client.close()

    @pytest.mark.asyncio
    async def test_set_osd_flag(self, mock_transport: MockTransport) -> None:
        """Test set_osd_flag."""
        client = SIYIClient(mock_transport)
        await client.connect()

        # Queue ACK
        ack_payload = b"\x01"
        ack_frame = Frame.build(0x4C, ack_payload, seq=0, need_ack=False)
        mock_transport.queue_response(ack_frame.to_bytes())

        result = await client.set_osd_flag(True)

        assert result is True

        await client.close()


class TestVideoCommands:
    """Test video stitching commands."""

    @pytest.mark.asyncio
    async def test_get_video_stitching_mode(self, mock_transport: MockTransport) -> None:
        """Test get_video_stitching_mode."""
        client = SIYIClient(mock_transport)
        await client.connect()

        # Queue ACK
        ack_payload = b"\x00"  # MODE_0
        ack_frame = Frame.build(0x10, ack_payload, seq=0, need_ack=False)
        mock_transport.queue_response(ack_frame.to_bytes())

        mode = await client.get_video_stitching_mode()

        assert mode == VideoStitchingMode.MODE_0

        await client.close()

    @pytest.mark.asyncio
    async def test_set_video_stitching_mode(self, mock_transport: MockTransport) -> None:
        """Test set_video_stitching_mode."""
        client = SIYIClient(mock_transport)
        await client.connect()

        # Queue ACK
        ack_payload = b"\x03"  # MODE_3
        ack_frame = Frame.build(0x11, ack_payload, seq=0, need_ack=False)
        mock_transport.queue_response(ack_frame.to_bytes())

        new_mode = await client.set_video_stitching_mode(VideoStitchingMode.MODE_3)

        assert new_mode == VideoStitchingMode.MODE_3

        await client.close()


class TestThermalCommands:
    """Test thermal imaging commands."""

    @pytest.mark.asyncio
    async def test_temp_at_point(self, mock_transport: MockTransport) -> None:
        """Test temp_at_point."""
        client = SIYIClient(mock_transport)
        await client.connect()

        # Queue ACK (6 bytes: temp, x, y)
        ack_payload = b"\x64\x00\x32\x00\x1e\x00"  # temp=100 (1.0°C), x=50, y=30
        ack_frame = Frame.build(0x12, ack_payload, seq=0, need_ack=False)
        mock_transport.queue_response(ack_frame.to_bytes())

        temp = await client.temp_at_point(50, 30, TempMeasureFlag.MEASURE_ONCE)

        assert isinstance(temp, TempPoint)
        assert temp.x == 50
        assert temp.y == 30
        assert temp.temperature_c == 1.0

        await client.close()

    @pytest.mark.asyncio
    async def test_temp_region(self, mock_transport: MockTransport) -> None:
        """Test temp_region."""
        client = SIYIClient(mock_transport)
        await client.connect()

        # Queue ACK (20 bytes)
        ack_payload = b"\x00\x00" * 10
        ack_frame = Frame.build(0x13, ack_payload, seq=0, need_ack=False)
        mock_transport.queue_response(ack_frame.to_bytes())

        temp = await client.temp_region((10, 10, 100, 100), TempMeasureFlag.MEASURE_ONCE)

        assert isinstance(temp, TempRegion)

        await client.close()

    @pytest.mark.asyncio
    async def test_temp_global(self, mock_transport: MockTransport) -> None:
        """Test temp_global."""
        client = SIYIClient(mock_transport)
        await client.connect()

        # Queue ACK (12 bytes)
        ack_payload = b"\x00\x00" * 6
        ack_frame = Frame.build(0x14, ack_payload, seq=0, need_ack=False)
        mock_transport.queue_response(ack_frame.to_bytes())

        temp = await client.temp_global(TempMeasureFlag.MEASURE_ONCE)

        assert isinstance(temp, TempGlobal)

        await client.close()

    @pytest.mark.asyncio
    async def test_get_pseudo_color(self, mock_transport: MockTransport) -> None:
        """Test get_pseudo_color."""
        client = SIYIClient(mock_transport)
        await client.connect()

        # Queue ACK
        ack_payload = b"\x00"  # WHITE_HOT
        ack_frame = Frame.build(0x1A, ack_payload, seq=0, need_ack=False)
        mock_transport.queue_response(ack_frame.to_bytes())

        color = await client.get_pseudo_color()

        assert color == PseudoColor.WHITE_HOT

        await client.close()

    @pytest.mark.asyncio
    async def test_set_pseudo_color(self, mock_transport: MockTransport) -> None:
        """Test set_pseudo_color."""
        client = SIYIClient(mock_transport)
        await client.connect()

        # Queue ACK
        ack_payload = b"\x03"  # IRONBOW
        ack_frame = Frame.build(0x1B, ack_payload, seq=0, need_ack=False)
        mock_transport.queue_response(ack_frame.to_bytes())

        new_color = await client.set_pseudo_color(PseudoColor.IRONBOW)

        assert new_color == PseudoColor.IRONBOW

        await client.close()

    @pytest.mark.asyncio
    async def test_get_thermal_output_mode(self, mock_transport: MockTransport) -> None:
        """Test get_thermal_output_mode."""
        client = SIYIClient(mock_transport)
        await client.connect()

        # Queue ACK
        ack_payload = b"\x00"  # FPS30
        ack_frame = Frame.build(0x33, ack_payload, seq=0, need_ack=False)
        mock_transport.queue_response(ack_frame.to_bytes())

        mode = await client.get_thermal_output_mode()

        assert mode == ThermalOutputMode.FPS30

        await client.close()

    @pytest.mark.asyncio
    async def test_set_thermal_output_mode(self, mock_transport: MockTransport) -> None:
        """Test set_thermal_output_mode."""
        client = SIYIClient(mock_transport)
        await client.connect()

        # Queue ACK
        ack_payload = b"\x01"  # FPS25_PLUS_TEMP
        ack_frame = Frame.build(0x34, ack_payload, seq=0, need_ack=False)
        mock_transport.queue_response(ack_frame.to_bytes())

        new_mode = await client.set_thermal_output_mode(ThermalOutputMode.FPS25_PLUS_TEMP)

        assert new_mode == ThermalOutputMode.FPS25_PLUS_TEMP

        await client.close()

    @pytest.mark.asyncio
    async def test_get_single_temp_frame(self, mock_transport: MockTransport) -> None:
        """Test get_single_temp_frame."""
        client = SIYIClient(mock_transport)
        await client.connect()

        # Queue ACK
        ack_payload = b"\x01"
        ack_frame = Frame.build(0x35, ack_payload, seq=0, need_ack=False)
        mock_transport.queue_response(ack_frame.to_bytes())

        result = await client.get_single_temp_frame()

        assert result is True

        await client.close()

    @pytest.mark.asyncio
    async def test_get_thermal_gain(self, mock_transport: MockTransport) -> None:
        """Test get_thermal_gain."""
        client = SIYIClient(mock_transport)
        await client.connect()

        # Queue ACK
        ack_payload = b"\x00"  # LOW
        ack_frame = Frame.build(0x37, ack_payload, seq=0, need_ack=False)
        mock_transport.queue_response(ack_frame.to_bytes())

        gain = await client.get_thermal_gain()

        assert gain == ThermalGain.LOW

        await client.close()

    @pytest.mark.asyncio
    async def test_set_thermal_gain(self, mock_transport: MockTransport) -> None:
        """Test set_thermal_gain."""
        client = SIYIClient(mock_transport)
        await client.connect()

        # Queue ACK
        ack_payload = b"\x01"  # HIGH
        ack_frame = Frame.build(0x38, ack_payload, seq=0, need_ack=False)
        mock_transport.queue_response(ack_frame.to_bytes())

        new_gain = await client.set_thermal_gain(ThermalGain.HIGH)

        assert new_gain == ThermalGain.HIGH

        await client.close()

    @pytest.mark.asyncio
    async def test_get_env_correction_params(self, mock_transport: MockTransport) -> None:
        """Test get_env_correction_params."""
        client = SIYIClient(mock_transport)
        await client.connect()

        # Queue ACK (10 bytes)
        ack_payload = b"\x00\x00" * 5
        ack_frame = Frame.build(0x39, ack_payload, seq=0, need_ack=False)
        mock_transport.queue_response(ack_frame.to_bytes())

        params = await client.get_env_correction_params()

        assert isinstance(params, EnvCorrectionParams)

        await client.close()

    @pytest.mark.asyncio
    async def test_set_env_correction_params(self, mock_transport: MockTransport) -> None:
        """Test set_env_correction_params."""
        client = SIYIClient(mock_transport)
        await client.connect()

        # Queue ACK
        ack_payload = b"\x01"
        ack_frame = Frame.build(0x3A, ack_payload, seq=0, need_ack=False)
        mock_transport.queue_response(ack_frame.to_bytes())

        params = EnvCorrectionParams(
            distance_m=10.0,
            emissivity_pct=95.0,
            humidity_pct=50.0,
            ambient_c=25.0,
            reflective_c=20.0,
        )

        result = await client.set_env_correction_params(params)

        assert result is True

        await client.close()

    @pytest.mark.asyncio
    async def test_get_env_correction_switch(self, mock_transport: MockTransport) -> None:
        """Test get_env_correction_switch."""
        client = SIYIClient(mock_transport)
        await client.connect()

        # Queue ACK
        ack_payload = b"\x01"
        ack_frame = Frame.build(0x3B, ack_payload, seq=0, need_ack=False)
        mock_transport.queue_response(ack_frame.to_bytes())

        switch = await client.get_env_correction_switch()

        assert switch is True

        await client.close()

    @pytest.mark.asyncio
    async def test_set_env_correction_switch(self, mock_transport: MockTransport) -> None:
        """Test set_env_correction_switch."""
        client = SIYIClient(mock_transport)
        await client.connect()

        # Queue ACK
        ack_payload = b"\x01"
        ack_frame = Frame.build(0x3C, ack_payload, seq=0, need_ack=False)
        mock_transport.queue_response(ack_frame.to_bytes())

        result = await client.set_env_correction_switch(True)

        assert result is True

        await client.close()

    @pytest.mark.asyncio
    async def test_get_ir_thresh_map_state(self, mock_transport: MockTransport) -> None:
        """Test get_ir_thresh_map_state."""
        client = SIYIClient(mock_transport)
        await client.connect()

        # Queue ACK
        ack_payload = b"\x00"
        ack_frame = Frame.build(0x42, ack_payload, seq=0, need_ack=False)
        mock_transport.queue_response(ack_frame.to_bytes())

        state = await client.get_ir_thresh_map_state()

        assert state is False

        await client.close()

    @pytest.mark.asyncio
    async def test_set_ir_thresh_map_state(self, mock_transport: MockTransport) -> None:
        """Test set_ir_thresh_map_state."""
        client = SIYIClient(mock_transport)
        await client.connect()

        # Queue ACK
        ack_payload = b"\x01"
        ack_frame = Frame.build(0x43, ack_payload, seq=0, need_ack=False)
        mock_transport.queue_response(ack_frame.to_bytes())

        result = await client.set_ir_thresh_map_state(True)

        assert result is True

        await client.close()

    @pytest.mark.asyncio
    async def test_get_ir_thresh_params(self, mock_transport: MockTransport) -> None:
        """Test get_ir_thresh_params."""
        client = SIYIClient(mock_transport)
        await client.connect()

        # Queue ACK (24 bytes: 3 regions * 8 bytes each)
        ack_payload = b"\x00" * 24
        ack_frame = Frame.build(0x44, ack_payload, seq=0, need_ack=False)
        mock_transport.queue_response(ack_frame.to_bytes())

        params = await client.get_ir_thresh_params()

        assert isinstance(params, IRThreshParams)

        await client.close()

    @pytest.mark.asyncio
    async def test_set_ir_thresh_params(self, mock_transport: MockTransport) -> None:
        """Test set_ir_thresh_params."""
        client = SIYIClient(mock_transport)
        await client.connect()

        # Queue ACK
        ack_payload = b"\x01"
        ack_frame = Frame.build(0x45, ack_payload, seq=0, need_ack=False)
        mock_transport.queue_response(ack_frame.to_bytes())

        region = IRThreshRegion(
            switch=1, temp_min=0, temp_max=100, color_r=255, color_g=0, color_b=0
        )
        params = IRThreshParams(region1=region, region2=region, region3=region)

        result = await client.set_ir_thresh_params(params)

        assert result is True

        await client.close()

    @pytest.mark.asyncio
    async def test_get_ir_thresh_precision(self, mock_transport: MockTransport) -> None:
        """Test get_ir_thresh_precision."""
        client = SIYIClient(mock_transport)
        await client.connect()

        # Queue ACK
        ack_payload = b"\x01"  # MAX
        ack_frame = Frame.build(0x46, ack_payload, seq=0, need_ack=False)
        mock_transport.queue_response(ack_frame.to_bytes())

        precision = await client.get_ir_thresh_precision()

        assert precision == IRThreshPrecision.MAX

        await client.close()

    @pytest.mark.asyncio
    async def test_set_ir_thresh_precision(self, mock_transport: MockTransport) -> None:
        """Test set_ir_thresh_precision."""
        client = SIYIClient(mock_transport)
        await client.connect()

        # Queue ACK
        ack_payload = b"\x02"  # MID
        ack_frame = Frame.build(0x47, ack_payload, seq=0, need_ack=False)
        mock_transport.queue_response(ack_frame.to_bytes())

        new_precision = await client.set_ir_thresh_precision(IRThreshPrecision.MID)

        assert new_precision == IRThreshPrecision.MID

        await client.close()

    @pytest.mark.asyncio
    async def test_manual_thermal_shutter(self, mock_transport: MockTransport) -> None:
        """Test manual_thermal_shutter."""
        client = SIYIClient(mock_transport)
        await client.connect()

        # Queue ACK
        ack_payload = b"\x01"
        ack_frame = Frame.build(0x4F, ack_payload, seq=0, need_ack=False)
        mock_transport.queue_response(ack_frame.to_bytes())

        result = await client.manual_thermal_shutter()

        assert result is True

        await client.close()


class TestLaserCommands:
    """Test laser ranging commands."""

    @pytest.mark.asyncio
    async def test_get_laser_distance(self, mock_transport: MockTransport) -> None:
        """Test get_laser_distance."""
        client = SIYIClient(mock_transport)
        await client.connect()

        # Queue ACK (2 bytes: raw = 1000 -> 100.0m)
        ack_payload = b"\xe8\x03"
        ack_frame = Frame.build(CMD_REQUEST_LASER_DISTANCE, ack_payload, seq=0, need_ack=False)
        mock_transport.queue_response(ack_frame.to_bytes())

        laser = await client.get_laser_distance()

        assert isinstance(laser, LaserDistance)
        assert laser.distance_m == 100.0

        await client.close()

    @pytest.mark.asyncio
    async def test_get_laser_target_latlon(self, mock_transport: MockTransport) -> None:
        """Test get_laser_target_latlon."""
        client = SIYIClient(mock_transport)
        await client.connect()

        # Queue ACK (8 bytes: lat_e7, lon_e7)
        ack_payload = b"\x00\x00\x00\x00\x00\x00\x00\x00"
        ack_frame = Frame.build(0x17, ack_payload, seq=0, need_ack=False)
        mock_transport.queue_response(ack_frame.to_bytes())

        latlon = await client.get_laser_target_latlon()

        assert isinstance(latlon, LaserTargetLatLon)

        await client.close()

    @pytest.mark.asyncio
    async def test_set_laser_ranging_state(self, mock_transport: MockTransport) -> None:
        """Test set_laser_ranging_state."""
        client = SIYIClient(mock_transport)
        await client.connect()

        # Queue ACK
        ack_payload = b"\x01"
        ack_frame = Frame.build(0x32, ack_payload, seq=0, need_ack=False)
        mock_transport.queue_response(ack_frame.to_bytes())

        result = await client.set_laser_ranging_state(True)

        assert result is True

        await client.close()


class TestAICommands:
    """Test AI tracking commands."""

    @pytest.mark.asyncio
    async def test_get_ai_mode(self, mock_transport: MockTransport) -> None:
        """Test get_ai_mode."""
        client = SIYIClient(mock_transport)
        await client.connect()

        # Queue ACK
        ack_payload = b"\x01"
        ack_frame = Frame.build(0x4D, ack_payload, seq=0, need_ack=False)
        mock_transport.queue_response(ack_frame.to_bytes())

        mode = await client.get_ai_mode()

        assert mode is True

        await client.close()

    @pytest.mark.asyncio
    async def test_get_ai_stream_status(self, mock_transport: MockTransport) -> None:
        """Test get_ai_stream_status."""
        client = SIYIClient(mock_transport)
        await client.connect()

        # Queue ACK
        ack_payload = b"\x01"  # STREAMING
        ack_frame = Frame.build(0x4E, ack_payload, seq=0, need_ack=False)
        mock_transport.queue_response(ack_frame.to_bytes())

        status = await client.get_ai_stream_status()

        assert status == AIStreamStatus.STREAMING

        await client.close()

    @pytest.mark.asyncio
    async def test_set_ai_stream_output(self, mock_transport: MockTransport) -> None:
        """Test set_ai_stream_output."""
        client = SIYIClient(mock_transport)
        await client.connect()

        # Queue ACK
        ack_payload = b"\x01"
        ack_frame = Frame.build(0x51, ack_payload, seq=0, need_ack=False)
        mock_transport.queue_response(ack_frame.to_bytes())

        result = await client.set_ai_stream_output(True)

        assert result is True

        await client.close()


class TestDebugCommands:
    """Test debug/ArduPilot commands."""

    @pytest.mark.asyncio
    async def test_get_control_mode(self, mock_transport: MockTransport) -> None:
        """Test get_control_mode."""
        client = SIYIClient(mock_transport)
        await client.connect()

        # Queue ACK
        ack_payload = b"\x00"  # ATTITUDE
        ack_frame = Frame.build(0x27, ack_payload, seq=0, need_ack=False)
        mock_transport.queue_response(ack_frame.to_bytes())

        mode = await client.get_control_mode()

        assert mode == ControlMode.ATTITUDE

        await client.close()

    @pytest.mark.asyncio
    async def test_get_weak_threshold(self, mock_transport: MockTransport) -> None:
        """Test get_weak_threshold."""
        client = SIYIClient(mock_transport)
        await client.connect()

        # Queue ACK (6 bytes)
        ack_payload = b"\x00\x00\x00\x00\x00\x00"
        ack_frame = Frame.build(0x28, ack_payload, seq=0, need_ack=False)
        mock_transport.queue_response(ack_frame.to_bytes())

        threshold = await client.get_weak_threshold()

        assert isinstance(threshold, WeakControlThreshold)

        await client.close()

    @pytest.mark.asyncio
    async def test_set_weak_threshold(self, mock_transport: MockTransport) -> None:
        """Test set_weak_threshold."""
        client = SIYIClient(mock_transport)
        await client.connect()

        # Queue ACK
        ack_payload = b"\x01"
        ack_frame = Frame.build(0x29, ack_payload, seq=0, need_ack=False)
        mock_transport.queue_response(ack_frame.to_bytes())

        threshold = WeakControlThreshold(limit=3.0, voltage=3.5, angular_error=10.0)

        result = await client.set_weak_threshold(threshold)

        assert result is True

        await client.close()

    @pytest.mark.asyncio
    async def test_get_motor_voltage(self, mock_transport: MockTransport) -> None:
        """Test get_motor_voltage."""
        client = SIYIClient(mock_transport)
        await client.connect()

        # Queue ACK (6 bytes)
        ack_payload = b"\x00\x00\x00\x00\x00\x00"
        ack_frame = Frame.build(0x2A, ack_payload, seq=0, need_ack=False)
        mock_transport.queue_response(ack_frame.to_bytes())

        voltage = await client.get_motor_voltage()

        assert isinstance(voltage, MotorVoltage)

        await client.close()

    @pytest.mark.asyncio
    async def test_get_weak_control_mode(self, mock_transport: MockTransport) -> None:
        """Test get_weak_control_mode."""
        client = SIYIClient(mock_transport)
        await client.connect()

        # Queue ACK
        ack_payload = b"\x00"
        ack_frame = Frame.build(0x70, ack_payload, seq=0, need_ack=False)
        mock_transport.queue_response(ack_frame.to_bytes())

        mode = await client.get_weak_control_mode()

        assert mode is False

        await client.close()

    @pytest.mark.asyncio
    async def test_set_weak_control_mode(self, mock_transport: MockTransport) -> None:
        """Test set_weak_control_mode."""
        client = SIYIClient(mock_transport)
        await client.connect()

        # Queue ACK (2 bytes: sta, weak_mode_state)
        ack_payload = b"\x01\x01"
        ack_frame = Frame.build(0x71, ack_payload, seq=0, need_ack=False)
        mock_transport.queue_response(ack_frame.to_bytes())

        result = await client.set_weak_control_mode(True)

        assert result is True

        await client.close()
