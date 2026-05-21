# Copyright (c) 2026 Mohamed Abdelkader <mohamedashraf123@gmail.com>
# All rights reserved.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

"""GStreamer RTSP backend using appsink — lowest latency, hardware acceleration.

The GStreamer pipeline decodes H.264 or H.265, converts to BGR, and feeds
frames into an appsink. A GLib.MainLoop runs in a daemon thread; the
new-sample signal handler posts frames to the asyncio event loop.
"""

from __future__ import annotations

import asyncio
import os
import threading
import time
from collections import deque
from collections.abc import AsyncGenerator
from typing import Final, Literal, cast

import structlog

# Jetson detection: /etc/nv_tegra_release exists only on L4T (Jetson) systems.
_IS_JETSON: Final[bool] = os.path.exists("/etc/nv_tegra_release")

try:
    import gi

    gi.require_version("Gst", "1.0")
    from gi.repository import Gst

    Gst.init(None)
    _GST_AVAILABLE = True
except Exception:  # gi not installed or version unavailable
    _GST_AVAILABLE = False

from .base import AbstractStreamBackend
from .models import StreamConfig, StreamFrame

_log: Final = structlog.get_logger(__name__)

_RECONNECT_DELAY_CAP: Final[float] = 30.0

# Desktop / generic pipeline. decodebin auto-negotiates H.264/H.265 from the
# RTSP SDP, videoconvert produces BGR on the CPU. Used on non-Jetson hosts.
_AUTO_PIPELINE = (
    "rtspsrc location={url} protocols={proto} latency={latency} buffer-mode=slave "
    "! decodebin "
    "! videoconvert "
    "! video/x-raw,format=BGR "
    "! queue max-size-buffers=1 leaky=downstream "
    "! appsink name=sink emit-signals=true max-buffers=1 drop=true sync=false"
)

# Jetson pipeline. Uses the NVIDIA hardware decoder (nvv4l2decoder) with DPB
# disabled for low latency, and nvvidconv to convert NV12→BGRx in hardware.
# CPU videoconvert is intentionally omitted — the appsink receives BGRx and
# the SDK strips the alpha channel in NumPy (fast view+copy). Saves a full
# per-frame CPU conversion that otherwise stalls on Orin-class devices.
_JETSON_PIPELINE = (
    "rtspsrc location={url} protocols={proto} latency={latency} buffer-mode=slave "
    "! rtp{codec}depay ! {codec}parse "
    "! nvv4l2decoder disable-dpb=true enable-max-performance=1 "
    "! nvvidconv ! video/x-raw,format=BGRx "
    "! queue max-size-buffers=1 leaky=downstream "
    "! appsink name=sink emit-signals=true max-buffers=1 drop=true sync=false"
)


class GStreamerBackend(AbstractStreamBackend):
    """GStreamer + appsink RTSP backend.

    Frames are extracted in the new-sample signal handler and dispatched to
    the asyncio queue. Bus messages are polled in a plain daemon thread instead
    of a GLib.MainLoop, keeping the GLib lock free for GTK3/cv2 in the main
    thread.

    Args:
        config: Stream configuration.
        codec: Codec hint; "h264" or "h265".

    Raises:
        ImportError: If PyGObject / GStreamer is not installed.
    """

    BACKEND_NAME: Final = "gstreamer"

    def __init__(
        self,
        config: StreamConfig,
        codec: Literal["h264", "h265"] = "h264",
    ) -> None:
        """Initialise the GStreamer backend.

        Args:
            config: Stream configuration.
            codec: Codec pipeline to use; "h264" or "h265".

        Raises:
            ImportError: If PyGObject is not available.
        """
        if not _GST_AVAILABLE:
            raise ImportError(
                "PyGObject and GStreamer are required for GStreamerBackend. "
                "Install system packages: gstreamer1.0-plugins-good gstreamer1.0-plugins-bad "
                "python3-gi, then: pip install PyGObject"
            )
        super().__init__(config)
        self._codec = codec
        self._loop: asyncio.AbstractEventLoop | None = None
        self._queue: asyncio.Queue[StreamFrame] | None = None
        self._latest: deque[StreamFrame] = deque(maxlen=1)
        self._pipeline: Gst.Pipeline | None = None
        self._glib_thread: threading.Thread | None = None
        self._stop_event = threading.Event()

    def _build_pipeline_str(self) -> str:
        """Build the GStreamer pipeline string from configuration.

        Resolution order:
          1. ``StreamConfig.pipeline`` override (verbatim, with {url} substituted).
          2. Jetson-tuned pipeline when running on L4T.
          3. Generic decodebin pipeline elsewhere.

        Returns:
            Pipeline description string suitable for gst_parse_launch.
        """
        if self._config.pipeline is not None:
            return self._config.pipeline.format(url=self._config.rtsp_url)

        proto = "tcp" if self._config.transport == "tcp" else "udp"
        template = _JETSON_PIPELINE if _IS_JETSON else _AUTO_PIPELINE
        return template.format(
            url=self._config.rtsp_url,
            proto=proto,
            latency=self._config.latency_ms,
            codec=self._codec,
        )

    async def connect(self) -> None:
        """Build the GStreamer pipeline and start the GLib main loop thread."""
        self._stop_event.clear()
        self._loop = asyncio.get_event_loop()
        self._queue = asyncio.Queue(maxsize=1)

        pipeline_str = self._build_pipeline_str()
        _log.info("gstreamer_pipeline", pipeline=pipeline_str)

        self._pipeline = Gst.parse_launch(pipeline_str)
        sink = self._pipeline.get_by_name("sink")
        sink.connect("new-sample", self._on_sample)

        bus = self._pipeline.get_bus()
        # Poll bus messages in a plain thread instead of a GLib.MainLoop.
        # A running GLib.MainLoop holds the GLib type-system lock, which blocks
        # GTK3 initialisation in the main thread (e.g. cv2.imshow). Polling
        # with timed_pop_filtered() achieves the same error/EOS detection
        # without occupying the GLib lock.
        self._glib_thread = threading.Thread(
            target=self._poll_bus,
            args=(bus,),
            name="siyi-gst-bus",
            daemon=True,
        )
        self._glib_thread.start()

        self._pipeline.set_state(Gst.State.PLAYING)
        _log.info("gstreamer_backend_connected", url=self._config.rtsp_url)

    async def disconnect(self) -> None:
        """Stop the pipeline and release resources."""
        self._stop_event.set()
        if self._pipeline is not None:
            self._pipeline.set_state(Gst.State.NULL)
            self._pipeline = None
        if self._glib_thread is not None:
            self._glib_thread.join(timeout=5.0)
            self._glib_thread = None
        _log.info("gstreamer_backend_disconnected")

    def frame_available(self) -> bool:
        """Return True if a frame is buffered.

        Returns:
            True when the latest deque contains a frame.
        """
        return bool(self._latest)

    def read_frame_nowait(self) -> StreamFrame | None:
        """Return the most recently decoded frame without blocking.

        Returns:
            Most recent StreamFrame, or None if none available.
        """
        return self._latest[-1] if self._latest else None

    async def frame_generator(self) -> AsyncGenerator[StreamFrame, None]:
        """Yield frames posted by the GStreamer appsink callback.

        Yields:
            StreamFrame objects in arrival order.
        """
        if self._queue is None:
            return
        while not self._stop_event.is_set():
            try:
                frame = await asyncio.wait_for(self._queue.get(), timeout=0.1)
                yield frame
            except asyncio.TimeoutError:
                continue

    def _poll_bus(self, bus: object) -> None:
        """Poll the GStreamer bus for error and EOS messages.

        Runs in a daemon thread. Uses timed_pop_filtered so no GLib.MainLoop
        is needed, keeping the GLib type-system lock free for the main thread.
        """
        gst_bus = cast("Gst.Bus", bus)
        interval = Gst.MSECOND * 100
        while not self._stop_event.is_set():
            msg = gst_bus.timed_pop_filtered(
                interval,
                Gst.MessageType.ERROR | Gst.MessageType.EOS,
            )
            if msg is None:
                continue
            if msg.type == Gst.MessageType.ERROR:
                err, _debug = msg.parse_error()
                _log.error("gst_pipeline_error", error=str(err))
                self._stop_event.set()
            elif msg.type == Gst.MessageType.EOS:
                _log.warning("gst_pipeline_eos")
                self._stop_event.set()

    def _on_sample(self, sink: object) -> object:
        """GStreamer appsink new-sample signal handler.

        Extracts the video buffer, converts to numpy BGR array, and dispatches
        to the asyncio queue via call_soon_threadsafe.

        Args:
            sink: The appsink element that emitted the signal.

        Returns:
            GLib flow return constant.
        """
        import numpy as np  # deferred so module loads without numpy at import time

        # Cast sink from object to GStreamer appsink type (Gst is Any via ignore_missing_imports).
        gst_sink = cast("Gst.Element", sink)
        try:
            sample = gst_sink.emit("pull-sample")
            buf = sample.get_buffer()
            caps = sample.get_caps()
            structure = caps.get_structure(0)
            width: int = structure.get_value("width")
            height: int = structure.get_value("height")
            fmt: str = structure.get_value("format") or "BGR"

            ok, map_info = buf.map(Gst.MapFlags.READ)
            if not ok:
                return Gst.FlowReturn.OK

            try:
                # Jetson hardware path emits BGRx (4ch). Strip alpha so all
                # backends deliver a 3-channel BGR frame to user code.
                channels = 4 if fmt == "BGRx" else 3
                raw = np.frombuffer(map_info.data, dtype=np.uint8).reshape(
                    height, width, channels
                )
                img = raw[:, :, :3].copy() if channels == 4 else raw.copy()
            finally:
                buf.unmap(map_info)

            sf = StreamFrame(
                frame=img,
                timestamp=time.monotonic(),
                width=width,
                height=height,
                backend=self.BACKEND_NAME,
            )
            self._latest.append(sf)

            _log.debug(
                "gst_frame_decoded",
                backend=self.BACKEND_NAME,
                width=width,
                height=height,
                timestamp=sf.timestamp,
            )

            loop = self._loop
            queue = self._queue
            if loop is not None and queue is not None:
                def _put(q: asyncio.Queue[StreamFrame] = queue, f: StreamFrame = sf) -> None:
                    try:
                        q.put_nowait(f)
                    except asyncio.QueueFull:
                        pass

                loop.call_soon_threadsafe(_put)

        except Exception as exc:
            _log.error("gst_sample_error", exc=type(exc).__name__, msg=str(exc))

        return Gst.FlowReturn.OK

