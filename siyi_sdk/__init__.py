# Copyright (c) 2026 Mohamed Abdelkader <mohamedashraf123@gmail.com>
# All rights reserved.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

"""SIYI Gimbal Camera External SDK Protocol — async Python SDK."""

from __future__ import annotations

from siyi_sdk.client import SIYIClient
from siyi_sdk.convenience import connect_serial, connect_tcp, connect_udp
from siyi_sdk.logging_config import configure_logging
from siyi_sdk.media import MediaClient
from siyi_sdk.models import MediaDirectory, MediaFile, MediaType
from siyi_sdk.stream import (
    CAMERA_GENERATION_MAP,
    CameraGeneration,
    SIYIStream,
    StreamBackend,
    StreamConfig,
    StreamFrame,
    build_rtsp_url,
)

__version__ = "0.6.0"
__all__ = [
    "CAMERA_GENERATION_MAP",
    "CameraGeneration",
    "MediaClient",
    "MediaDirectory",
    "MediaFile",
    "MediaType",
    "SIYIClient",
    "configure_logging",
    "SIYIStream",
    "StreamBackend",
    "StreamConfig",
    "StreamFrame",
    "build_rtsp_url",
    "connect_serial",
    "connect_tcp",
    "connect_udp",
]
