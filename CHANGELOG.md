# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.6.0] - 2026-06-05

### Added

- **Fire-and-forget gimbal control** for high-rate (50–100 Hz) control
  loops such as visual servoing:
  - `SIYIClient.rotate_nowait(yaw, pitch)` — velocity command without
    ACK round-trip or per-CMD_ID lock contention (0x07).
  - `SIYIClient.set_attitude_nowait(yaw_deg, pitch_deg)` — absolute
    attitude setpoint without ACK (0x0E).
  - `SIYIClient.set_single_axis_nowait(axis, angle_deg)` — single-axis
    variant (0x41).
- A8 mini mechanical-limit constants in `siyi_sdk.constants`:
  `A8MINI_YAW_MIN_DEG`, `A8MINI_YAW_MAX_DEG`,
  `A8MINI_PITCH_MIN_DEG`, `A8MINI_PITCH_MAX_DEG`,
  `GIMBAL_RATE_CMD_MIN`, `GIMBAL_RATE_CMD_MAX`.
- Unit tests for all `_nowait` methods, including a 200-frame
  back-to-back burst test that verifies the per-CMD_ID lock is
  bypassed (would deadlock if it were not).
- Quickstart documentation: new "High-rate control (fire-and-forget)"
  section in `docs/quickstart.md`.

### Notes

- These additions are purely additive and backwards-compatible. The
  existing `rotate()`, `set_attitude()`, and `set_single_axis()`
  methods are unchanged and still wait for the ACK.

## [0.5.0] - 2026-04-22

### Added

- **Resilient Web UI**: Refactored the dashboard to use static assets (`static/`) for improved
  loading reliability and cache management.
- **Licensing**: Added the MIT MISSION `LICENSE` file to the repository.
- **Copyright Compliance**: Added standard copyright headers to all source files (`siyi_sdk`,
  `examples`, `tests`, `web_ui`) using a new `scripts/add_copyright.py` utility.

### Fixed

- Resolved Web UI initialization hangs by decoupling frontend logic from the main HTML page.
- Improved GStreamer dependency documentation and installation script.

## [0.4.0] - 2026-04-22

### Added

- **Web UI Dashboard**: A new, interactive web-based dashboard for controlling the gimbal,
  camera, and viewing streaming video directly in the browser.
- New `web` optional dependency group in `pyproject.toml` including `fastapi`, `uvicorn`,
  and `pydantic`.
- Comprehensive Web UI documentation in `docs/WEB_UI.md`.
- Status indicators and firmware version display in the Web UI.
- Auto-recovery and connection monitoring in the Web UI backend.

## [0.3.0] - 2026-04-22

### Added

- `MediaClient` in `siyi_sdk.media`: Async HTTP client for the camera web-server media API (port 82).
  Supports listing directories, file counting, and paginated file listing with download URLs.
- New models in `siyi_sdk.models`: `MediaType`, `MediaDirectory`, `MediaFile`.
- `ProductID.label` property for human-readable product names (e.g. "A8 Mini").
- `FirmwareVersion.format_word()` static helper for pretty-printing firmware versions.
- Documentation for Media HTTP API in `docs/media_http_api.md`.
- 11+ new example scripts in `examples/` covering zoom, focus, thermal imaging, gimbal scanning,
  attitude control loops, and system information.
- `examples/README.md` with usage instructions for the new suite of examples.
- `SIYI_SDK_PROTOCOL.txt` protocol reference file.

### Changed

- **Improved Client Robustness**: `SIYIClient` now catches and logs `CRCError` and `FramingError`
  during the receive loop, skipping malformed packets rather than crashing the reader task.
- **Better Product ID Decoding**: `HardwareID.product_id` now correctly parses the product code
  from ASCII hex in the hardware ID string, fixing identification for A8 Mini (0x73) and others.
- **Enhanced Reliability**:
  - Increased `default_timeout` to 2.0s and `max_retries` to 2 for better stability on unstable links.
  - Added `ONE_KEY_CENTERING`, `SET_ATTITUDE`, and `SET_SINGLE_AXIS` to idempotent retry list.
- **Streaming Optimizations**:
  - `GStreamerBackend`: Unified pipeline using `decodebin` for automatic H.264/H.265 negotiation.
  - `OpenCVBackend`: Added aggressive low-latency FFmpeg flags (`nobuffer`, `low_delay`, `framedrop`).
  - Improved thread-safe frame delivery to asyncio queues in both backends.

### Fixed

- Fallback to `get_current_zoom()` in `manual_zoom()` when cameras (like A8 Mini) don't ACK a
  stop command (direction=0) while not actively zooming.

## [0.2.2] - 2026-04-22

### Added

- `configure_logging()` is now exported from the top-level `siyi_sdk` package so
  examples and user scripts can import it directly:
  `from siyi_sdk import configure_logging`.
- New `fmt` parameter on `configure_logging()`: `"console"` (default) renders
  human-readable output with timestamp, coloured log-level label, event name, and
  `key=value` pairs; `"json"` keeps the original machine-readable JSON output.
  The format is also selectable via the `SIYI_LOG_FORMAT` environment variable
  (`console` | `json`).

### Changed

- All 11 example scripts now call `configure_logging(level="INFO")` before
  `asyncio.run(main())`.  This gives every example run structured, human-readable
  log output including visible level labels (`[info]`, `[warning]`, `[error]`,
  `[debug]`) alongside the existing `print()` output.  Previously the examples
  silently suppressed SDK logs (WARNING threshold) and did not configure the log
  format at all, resulting in raw JSON blobs appearing on stderr.
- Console renderer uses local-time `HH:MM:SS` timestamps (instead of UTC ISO-8601)
  for readability.  JSON renderer retains UTC ISO-8601 timestamps.

## [0.2.1] - 2026-04-20

### Added

- `siyi_sdk.stream` sub-package: RTSP video streaming with OpenCV, GStreamer, and aiortsp+PyAV backends
- `SIYIStream` async class with callback-based frame delivery and auto-reconnect
- `build_rtsp_url()` helper covering old-gen (`/main.264`) and new-gen (`/video1`, `/video2`) cameras
- `CameraGeneration` enum and `CAMERA_GENERATION_MAP` lookup
- `SIYIClient.create_stream()` convenience factory
- Six runnable examples in `examples/`: `rtsp_opencv_new_gen.py`, `rtsp_opencv_old_gen.py`,
  `rtsp_gstreamer.py`, `rtsp_sub_stream.py`, `rtsp_record.py`, `rtsp_with_control.py`
- `docs/streaming.md` comprehensive streaming guide
- Optional dependency groups: `stream`, `stream-opencv`, `stream-gst`, `stream-aiortsp`
- Convenience script `install_gst_dependencies.sh` for Ubuntu/Debian and updated docs noting `PyGObject` build requirements

## [0.1.0] - 2026-04-20

### Added

- **Phase 7 — Final QA** (Release gate audit):
  - Static analysis: ruff check and ruff format pass with zero violations.
  - Type checking: mypy --strict passes with zero errors.
  - Test suite: 500+ tests passing covering protocol, commands, transport,
    client, and integration scenarios.
  - Build: Successfully produces `siyi_sdk-0.1.0-py3-none-any.whl` and
    `siyi_sdk-0.1.0.tar.gz`, both pass `twine check`.
  - Fixed mypy strict errors in client.py (callback variable typing, encode_single_axis argument order).
  - Fixed ruff issues (ambiguous Unicode characters, line lengths, import sorting).
  - Fixed integration tests to match actual SIYIClient API.
  - Updated test fixtures for structlog output capture.

- **Phase 6 — Documentation and Release** (TASK-070 through TASK-073):
  - `docs/quickstart.md`: UDP, TCP, and Serial connection examples with MockTransport testing.
  - `docs/protocol.md`: Complete protocol reference mirroring Appendices A/B/D/E of the specification including frame structure (ASCII diagram), command catalogue (80+ CMD_IDs), CRC-16/XMODEM algorithm with 7 test vectors, timing and heartbeat requirements, and 14 known quirks (CRC seed, CTRL reserved bits, SEQ wrapping, firmware byte interpretation, retry logic, TCP heartbeat, laser out-of-range, A2 mini yaw, per-CMD_ID locking, RC deprecation, float endianness, product-specific no-response, resolution validation, reserved CMD_IDs).
  - `examples/udp_heartbeat.py`: Connect to gimbal over UDP and read firmware + attitude.
  - `examples/set_attitude.py`: Move gimbal to target angles and return to centre.
  - `examples/subscribe_attitude_stream.py`: Subscribe to attitude push stream at 10 Hz.
  - `examples/thermal_spot_temperature.py`: Read spot temperature at pixel coordinates.
  - `examples/laser_ranging.py`: Enable laser ranging and poll distance for 5 seconds.
  - `README.md`: Full rewrite with badges (PyPI, CI, coverage, MIT), description of supported products, installation instructions (pip + uv), comprehensive quickstart, API reference table (80+ methods organized by category), environment variable configuration (SIYI_LOG_LEVEL, SIYI_PROTOCOL_TRACE), examples directory, development setup, and links to documentation.
  - `pyproject.toml`: Bumped version from 0.0.0 to 0.1.0, development status from Alpha (3) to Beta (4), fixed homepage and repository URLs to mzahana/siyi-sdk.
  - CHANGELOG.md: Fully populated [0.1.0] section dated 2026-04-20 with complete Added/Changed summary across all 6 phases.

- **Phase 2 — Transport layer** (TASK-020 through TASK-025):
  - `siyi_sdk/transport/base.py`: `AbstractTransport` ABC defining the transport
    interface (`connect`, `close`, `send`, `stream`, `is_connected`,
    `supports_heartbeat`) and `Unsubscribe` type alias.
  - `siyi_sdk/transport/mock.py`: `MockTransport` for testing — FIFO
    `queue_response` / `queue_error`, `sent_frames` capture, configurable
    `supports_heartbeat`.
  - `siyi_sdk/transport/udp.py`: `UDPTransport` built on
    `asyncio.DatagramProtocol`; defaults to `192.168.144.25:37260`;
    `supports_heartbeat = False`.
  - `siyi_sdk/transport/tcp.py`: `TCPTransport` built on
    `asyncio.open_connection`; `supports_heartbeat = True` (1 Hz heartbeat
    driven by the client layer).
  - `siyi_sdk/transport/serial.py`: `SerialTransport` using
    `pyserial-asyncio` (8-N-1 @ 115200 baud default); `supports_heartbeat = False`.
  - OS-level errors wrapped in SDK-specific `ConnectionError` / `SendError` /
    `NotConnectedError`.
  - Structured logging via `structlog` on connect / disconnect / send / receive.
  - `tests/transport/test_{base,mock,udp,tcp,serial}.py`: 50 tests total
    (43 passing, 7 serial tests auto-skip when `socat` is unavailable);
    loopback UDP echo server, `asyncio.start_server` TCP echo, and `socat`
    pty-pair fixtures for round-trip validation.
  - Coverage: mock 97 %, tcp 86 %, udp 86 %, base 100 % (overall transport
    module ≈ 79 % including the socat-gated serial branches).

- **Phase 3 — Command layer** (TASK-030 through TASK-041):
  - `siyi_sdk/commands/system.py`: Encoders/decoders for heartbeat (0x00),
    firmware version (0x01), hardware ID (0x02), UTC time (0x30), system info
    (0x31), system time (0x40), soft reboot (0x80), and IP config (0x81–0x82).
  - `siyi_sdk/commands/focus.py`: Auto-focus (0x04) and manual focus (0x06)
    commands with coordinate validation.
  - `siyi_sdk/commands/zoom.py`: Manual zoom (0x05), absolute zoom (0x0F),
    zoom range (0x16), and current zoom (0x18) commands with decimal precision
    handling.
  - `siyi_sdk/commands/gimbal.py`: Gimbal rotation (0x07), one-key centering
    (0x08), set attitude (0x0E), gimbal mode (0x19), and single-axis control
    (0x41) with angle validation.
  - `siyi_sdk/commands/attitude.py`: Gimbal attitude (0x0D), aircraft attitude
    (0x22), FC/gimbal data streams (0x24–0x25), magnetic encoder (0x26), and
    raw GPS (0x3E) with proper float/int32 handling.
  - `siyi_sdk/commands/camera.py`: Camera system info (0x0A), function feedback
    (0x0B), capture (0x0C), encoding params (0x20–0x21), SD card format (0x48),
    picture name type (0x49–0x4A), and HDMI OSD (0x4B–0x4C).
  - `siyi_sdk/commands/video.py`: Video stitching mode get/set (0x10–0x11).
  - `siyi_sdk/commands/thermal.py`: Complete thermal imaging suite including
    temperature measurement (0x12–0x14), pseudo color (0x1A–0x1B), output mode
    (0x33–0x34), gain (0x37–0x38), environmental correction (0x39–0x3C), IR
    threshold mapping (0x42–0x47), and manual shutter (0x4F).
  - `siyi_sdk/commands/laser.py`: Laser distance (0x15), target lat/lon (0x17),
    and ranging state (0x32) with out-of-range handling.
  - `siyi_sdk/commands/rc.py`: RC channels (0x23) with 18-channel support.
  - `siyi_sdk/commands/debug.py`: Control mode (0x27), weak thresholds
    (0x28–0x29), motor voltage (0x2A), and weak control mode (0x70–0x71).
  - `siyi_sdk/commands/ai.py`: AI mode (0x4D), tracking stream status (0x4E),
    tracking push (0x50), and stream output (0x51).
  - All encoders validate input ranges and raise `ConfigurationError` on invalid
    parameters.
  - All decoders validate payload length and raise `MalformedPayloadError` on
    mismatches.
  - Decoders with status bytes raise `ResponseError(cmd_id, sta)` when `sta == 0`.
  - Comprehensive test suite with 208 tests covering round-trip encoding,
    byte-exact Chapter 4 fixtures, boundary conditions, error cases, and enum
    validation.
  - Test coverage: 84.55% overall (12 modules at 95%+, including focus.py,
    gimbal.py, zoom.py at 94–100%).
  - Verified byte-exact protocol compliance: `auto_focus(1, 300, 100)` →
    `01 2C 01 64 00`, `rotate(100, 100)` → `64 64`, `absolute_zoom(4.5)` →
    `04 05`, `set_attitude(-90.0, 0.0)` → `7C FC 00 00`.

- **Phase 4 — Client API** (TASK-050 through TASK-057):
  - `siyi_sdk/client.py`: `SIYIClient` class — fully async high-level API with
    ~75 public methods (one per protocol command).
  - **Concurrency control**: Per-CMD_ID `asyncio.Lock` serializes concurrent
    requests sharing the same CMD_ID; pending futures registry keyed by CMD_ID
    (protocol ACKs carry CMD_ID only, not SEQ).
  - **Request-response**: `_send_command()` builds frames with auto-incrementing
    SEQ (wraps 0xFFFF → 0x0000), registers future, acquires CMD_ID lock, sends,
    waits with timeout.
  - **Retry logic**: Idempotent reads (`Request*` / `Get*` commands) retry once
    on `TimeoutError`; write commands (`Set*` / `Send*`) fail immediately to
    prevent unintended side effects.
  - **Receive loop**: `_reader()` async-iterates `transport.stream()`, feeds
    `FrameParser`, and dispatches parsed frames to stream callbacks (0x0D, 0x0B,
    0x15, 0x26, 0x2A, 0x50) or resolves pending futures.
  - **Heartbeat**: `_heartbeat()` task sends `HEARTBEAT_FRAME` every 1 s when
    `transport.supports_heartbeat == True` (TCP only); stopped on close.
  - **Stream subscriptions**: `on_attitude()`, `on_laser_distance()`,
    `on_function_feedback()`, `on_ai_tracking()` register callbacks and return
    `Unsubscribe` closures; subscriptions activated via `request_gimbal_stream()`
    / `request_fc_stream()`.
  - **Auto-reconnect**: Optional exponential backoff (0.5/1/2/4/8 s, max 5
    attempts); replays active stream subscriptions on successful reconnect;
    emits `connection_event` on success/failure.
  - **Fire-and-forget commands**: 0x0C (capture), 0x22 (aircraft attitude),
    0x23 (RC channels), 0x3E (raw GPS) send without waiting for ACK per protocol.
  - **Context manager**: `async with SIYIClient(transport) as client: ...`
    handles connect/close lifecycle.
  - `siyi_sdk/convenience.py`: Factory functions `connect_udp()`,
    `connect_tcp()`, `connect_serial()` — construct transport + client,
    connect, and return ready-to-use client.
  - **Comprehensive test suite**: 89 test methods in `tests/test_client.py`
    covering lifecycle, sequence number management (including 70k uniqueness
    property test), command execution (happy path, timeouts, retries,
    concurrency), stream subscriptions, fire-and-forget commands, and full
    coverage of all public API methods organized by category (system, focus,
    zoom, gimbal, attitude, camera, video, thermal, laser, AI, debug).
  - `tests/test_convenience.py`: Tests for factory functions with loopback UDP
    echo server, `asyncio.start_server` TCP, and `socat` serial (auto-skipped
    if unavailable).
  - Test coverage: 90%+ for `client.py` and `convenience.py`.
  - All tests passing with mypy strict compliance and ruff format/check zero
    violations.

- **Phase 5 — Test suite and integration** (TASK-060 through TASK-063):
  - **Integration tests** (`tests/integration/`): 34 tests covering full-flow
    scenarios (connect → firmware → attitude → rotate → close), streaming
    subscriptions (on_attitude, on_laser_distance), error recovery (CRC
    corruption, response errors), fire-and-forget commands, retry logic,
    multi-client scenarios, and auto-reconnect.
  - **Concurrency tests**: 7 tests validating concurrent distinct commands,
    same-CMD_ID serialization, sequence number isolation across clients,
    response routing with concurrent operations, and high concurrency (100
    simultaneous requests).
  - **Logging tests** (`tests/test_logging.py`): 12 tests with
    `structlog.testing.capture_logs()` verifying log levels, hexdump processor,
    command dispatch events, error logging (CRC/timeout/response errors), and
    transport logging.
  - **Hardware-in-the-loop scaffolding** (`tests/hil/test_udp_live.py`): 8
    tests for real device validation — gated with `@pytest.mark.hil` and
    `SIYI_HIL=1` environment variable; includes device reachability checks, UDP
    ping, firmware version, attitude retrieval, and connection lifecycle tests.
  - **Benchmark tests** (`tests/benchmarks/test_parser_throughput.py`): Parser
    achieves ~1.8–2.3 MB/s throughput on 10 MB random frame blob; results
    stored in `tests/benchmarks/results.json`.
  - **Property-based tests**: Expanded `tests/property/test_frame_roundtrip.py`
    and `test_parser_fuzz.py` to 10,000 examples each with 60-second deadline
    per hypothesis spec.
  - **Comprehensive fixtures** (`tests/conftest.py`): 444 lines with fixtures
    for all CMD_IDs, event loop management, mock transport, and connected client
    setup.
  - **Coverage targets met**:
    - `constants.py`: 100% ✓
    - `models.py`: 100% ✓
    - `exceptions.py`: 100% ✓
    - `logging_config.py`: 96% (near 100%)
    - `protocol/crc.py`: 100% branch ✓
    - `protocol/frame.py`: 100% line, 100% branch ✓
    - `protocol/parser.py`: 99% (one edge branch)
    - `commands/*.py`: 72–100% line (all enum members round-tripped)
    - `transport/mock.py`: 97% ✓
    - Overall package coverage: **73%** (510 tests passing)
  - Added `UINT64_MAX` constant to eliminate magic hex literal in `system.py`.
  - `pytest.ini` configured with markers for `hil`, `property`, and `benchmark`.

### Changed

- `siyi_sdk/__init__.py`: Bumped `__version__` from "0.0.0" to "0.1.0".
- `pyproject.toml`: Updated version to "0.1.0", changed development status classifier from 3 - Alpha to 4 - Beta, and corrected project URLs to use mzahana GitHub namespace instead of placeholder OWNER.
- `siyi_sdk/transport/__init__.py`: re-exports `AbstractTransport`,
  `Unsubscribe`, `MockTransport`, `UDPTransport`, `TCPTransport`,
  `SerialTransport`.
- `siyi_sdk/commands/__init__.py`: re-exports all 172 encoder/decoder functions
  from command modules.

## [0.0.1] - 2026-04-20

### Added

- Initial project scaffolding (pyproject, CI, empty package layout, logging config).
- **Phase 1 — Protocol foundation**: `constants.py` (STX, default endpoints,
  `HEARTBEAT_FRAME`, CMD IDs), `models.py` (frame / command dataclasses),
  `exceptions.py` (SDK exception hierarchy), `protocol/crc.py`
  (CRC-16/XMODEM, poly 0x1021, seed 0x0000), `protocol/frame.py` (encode /
  decode of the SIYI wire frame), `protocol/parser.py` (streaming
  `FrameParser`), and `logging_config.py` (structlog setup).
