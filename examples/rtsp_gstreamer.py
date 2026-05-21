# Copyright (c) 2026 Mohamed Abdelkader <mohamedashraf123@gmail.com>
# All rights reserved.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

"""GStreamer low-latency RTSP streaming example for old-generation cameras.

Demonstrates the GStreamer backend which provides hardware-accelerated H.264
decoding and the lowest end-to-end latency among available backends.

Target cameras: ZR30, ZR10, A8 Mini, A2 Mini, R1M (old-gen, H.264 stream).
Stream URL: rtsp://192.168.144.25:8554/main.264

GStreamer pipeline used internally (desktop):
    rtspsrc location=<url> protocols=tcp latency=100 buffer-mode=slave
    ! decodebin ! videoconvert ! video/x-raw,format=BGR
    ! queue max-size-buffers=1 leaky=downstream
    ! appsink name=sink emit-signals=true max-buffers=1 drop=true sync=false

GStreamer pipeline used internally (Jetson / L4T):
    rtspsrc location=<url> protocols=tcp latency=100 buffer-mode=slave
    ! rtph264depay ! h264parse
    ! nvv4l2decoder disable-dpb=true enable-max-performance=1
    ! nvvidconv ! video/x-raw,format=BGRx
    ! queue max-size-buffers=1 leaky=downstream
    ! appsink name=sink emit-signals=true max-buffers=1 drop=true sync=false

Prerequisites:
    sudo apt install gstreamer1.0-plugins-good gstreamer1.0-plugins-bad python3-gi
    pip install PyGObject opencv-python
"""

from __future__ import annotations

import asyncio
import os
import threading
import time

# Prevent Qt from using GLib's event dispatcher, which conflicts with the
# GLib main loop that GStreamer runs in a background thread.
os.environ.setdefault("QT_NO_GLIB", "1")

from siyi_sdk import (
    CameraGeneration,
    SIYIStream,
    StreamBackend,
    StreamConfig,
    StreamFrame,
    build_rtsp_url,
    configure_logging,
)


def main() -> None:
    try:
        import cv2  # type: ignore[import]
    except ImportError:
        print("opencv-python is required. Install with: pip install opencv-python")
        return

    rtsp_url = build_rtsp_url(generation=CameraGeneration.OLD, stream="main")
    print(f"GStreamer backend connecting to: {rtsp_url}")

    config = StreamConfig(
        rtsp_url=rtsp_url,
        backend=StreamBackend.GSTREAMER,
        latency_ms=100,
        codec="h264",
    )
    stream = SIYIStream(config)

    # Shared state between asyncio thread and main (display) thread.
    latest_frame: list[StreamFrame | None] = [None]
    frame_count: list[int] = [0]
    stop_event = threading.Event()

    def on_frame(frame: StreamFrame) -> None:
        frame_count[0] += 1
        latest_frame[0] = frame

    stream.on_frame(on_frame)

    async def _run() -> None:
        await stream.start()
        while not stop_event.is_set():
            await asyncio.sleep(0.05)
        await stream.stop()

    # Create the window on the main thread before the asyncio thread starts the
    # GLib main loop. GTK3 (cv2's display backend on Linux) must be initialised
    # from the main thread; if the GLib loop is already running in another
    # thread when imshow first tries to init GTK, it deadlocks.
    cv2.namedWindow("SIYI GStreamer Stream", cv2.WINDOW_NORMAL)
    cv2.waitKey(1)

    asyncio_thread = threading.Thread(
        target=asyncio.run,
        args=(_run(),),
        name="siyi-asyncio",
        daemon=True,
    )
    asyncio_thread.start()

    # All cv2 display happens on the main thread — no GLib/Qt conflicts.
    try:
        print("Streaming started. Press 'q' or Ctrl+C to stop.")
        last_print = time.monotonic()
        while True:
            frame = latest_frame[0]
            if frame is not None:
                cv2.imshow("SIYI GStreamer Stream", frame.frame)
            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                break
            now = time.monotonic()
            if now - last_print >= 1.0:
                fps = stream.fps
                print(f"FPS (rolling 1s): {fps:.1f}  total frames: {frame_count[0]}")
                last_print = now
    except KeyboardInterrupt:
        pass
    finally:
        stop_event.set()
        asyncio_thread.join(timeout=5.0)
        cv2.destroyAllWindows()
        print(f"Stream stopped. Total frames received: {frame_count[0]}")


if __name__ == "__main__":
    configure_logging(level="INFO")
    main()
