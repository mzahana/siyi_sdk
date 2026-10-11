# Copyright (c) 2026 Mohamed Abdelkader <mohamedashraf123@gmail.com>
# All rights reserved.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import asyncio
import logging
import json
import os
from typing import Optional, AsyncGenerator
from contextlib import asynccontextmanager

import cv2
import numpy as np
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Request
from fastapi.responses import StreamingResponse, HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from siyi_sdk import (
    SIYIClient,
    MediaClient,
    SIYIStream,
    StreamConfig,
    StreamBackend,
    MediaType,
    CameraGeneration,
    build_rtsp_url,
    configure_logging,
)
from siyi_sdk.exceptions import TimeoutError
from siyi_sdk.transport.udp import UDPTransport
from siyi_sdk.models import (
    CenteringAction,
    CaptureFuncType,
    GimbalDataType,
    DataStreamFreq,
    StreamType,
    FirmwareVersion,
    HardwareID
)

# Setup logging
configure_logging(level="INFO")
logger = logging.getLogger(__name__)

# Global state
GLOBAL_CONFIG = {
    "camera_ip": "192.168.144.25",
    "port": 8082,
}

class CameraState:
    def __init__(self):
        self.client: Optional[SIYIClient] = None
        self.media: Optional[MediaClient] = None
        self.stream: Optional[SIYIStream] = None
        self.latest_frame: Optional[bytes] = None
        self.frame_event = asyncio.Event()
        self.attitude = {"yaw": 0.0, "pitch": 0.0, "roll": 0.0}
        self.lock = asyncio.Lock()
        self.is_connected = False
        self.watchdog_task: Optional[asyncio.Task] = None
        self.ip: Optional[str] = None
        self.live_enabled = True
        self.stop_event = asyncio.Event() # For clean shutdown

    async def initialize(self, ip: str):
        async with self.lock:
            # Shutdown existing clients first
            await self.shutdown()
            
            # Reset state for new initialization
            self.stop_event.clear()
            self.ip = ip
            self.is_connected = False
            
            logger.info(f"Initializing clients for IP: {ip}")
            transport = UDPTransport(ip)
            self.client = SIYIClient(transport)
            self.media = MediaClient(ip)
            
            # Initialize Video Stream
            rtsp_url = build_rtsp_url(host=ip, generation=CameraGeneration.OLD, stream="main")
            config = StreamConfig(
                rtsp_url=rtsp_url,
                backend=StreamBackend.GSTREAMER,
                latency_ms=100,
                codec="h265",
            )
            self.stream = SIYIStream(config)
            self.stream.on_frame(self._on_frame)
            
            if self.watchdog_task:
                self.watchdog_task.cancel()
            self.watchdog_task = asyncio.create_task(self.watchdog())

    async def watchdog(self):
        """Background task to monitor camera and auto-recover."""
        consecutive_failures = 0
        while True:
            try:
                if self.client and self.ip:
                    try:
                        # Attempt to connect and ping
                        if not self.is_connected:
                            await asyncio.wait_for(self.client.connect(), timeout=5.0)
                            await asyncio.wait_for(
                                self.client.request_gimbal_stream(GimbalDataType.ATTITUDE, DataStreamFreq.HZ10),
                                timeout=2.0
                            )
                            self.client.on_attitude(self._on_attitude)
                        
                        await asyncio.wait_for(self.client.get_firmware_version(), timeout=2.0)
                        
                        if not self.is_connected:
                            logger.info("Camera connection restored")
                            self.is_connected = True
                            consecutive_failures = 0
                            # Recover stream if it was supposed to be running
                            if self.live_enabled:
                                if self.stream and not self.stream.is_running:
                                    logger.info("Watchdog: Restarting stream...")
                                    await asyncio.wait_for(self.stream.start(), timeout=10.0)
                    except Exception as e:
                        logger.debug(f"Watchdog ping failed: {e}")
                        consecutive_failures += 1
                        if consecutive_failures >= 2 and self.is_connected:
                            logger.warning("Camera connection lost (Watchdog)")
                            self.is_connected = False
                            if self.stream:
                                await asyncio.wait_for(self.stream.stop(), timeout=3.0)
                
                await asyncio.sleep(2) # Faster polling
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Watchdog loop crash: {e}")
                await asyncio.sleep(5)

    def _on_attitude(self, att):
        self.attitude = {
            "yaw": att.yaw_deg,
            "pitch": att.pitch_deg,
            "roll": att.roll_deg
        }

    def _on_frame(self, frame):
        # Encode to JPEG for MJPEG stream
        success, buffer = cv2.imencode('.jpg', frame.frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
        if success:
            self.latest_frame = buffer.tobytes()
            self.frame_event.set()

    async def shutdown(self):
        self.stop_event.set()
        if self.watchdog_task:
            self.watchdog_task.cancel()
            try:
                await asyncio.wait_for(self.watchdog_task, timeout=2.0)
            except (asyncio.CancelledError, asyncio.TimeoutError):
                pass
            self.watchdog_task = None
            
        if self.stream:
            try:
                await asyncio.wait_for(self.stream.stop(), timeout=3.0)
            except Exception:
                pass
            self.stream = None
        if self.client:
            try:
                await asyncio.wait_for(self.client.close(), timeout=2.0)
            except Exception:
                pass
            self.client = None
        if self.media:
            self.media = None
        logger.info("Clients shut down")

    async def restart_stream(self):
        async with self.lock:
            if self.stream:
                logger.info("Restarting video stream...")
                await self.stream.stop()
                # Use current config to restart
                await asyncio.sleep(1.0) # Small delay
                await self.stream.start()
                logger.info("Video stream restarted")

    async def toggle_stream(self, enabled: bool):
        async with self.lock:
            self.live_enabled = enabled
            if not self.stream:
                return
            if enabled and not self.stream.is_running and self.is_connected:
                logger.info("Starting backend stream...")
                await asyncio.wait_for(self.stream.start(), timeout=10.0)
            elif not enabled and self.stream.is_running:
                logger.info("Stopping backend stream (deep sleep)...")
                await asyncio.wait_for(self.stream.stop(), timeout=5.0)

state = CameraState()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load initial config or use default
    await state.initialize(GLOBAL_CONFIG["camera_ip"])
    yield
    await state.shutdown()

app = FastAPI(lifespan=lifespan)

# Models
class IPConfigRequest(BaseModel):
    ip: str

class RotateRequest(BaseModel):
    yaw: int
    pitch: int

class EncodingRequest(BaseModel):
    # Simplified for UI
    resolution: Optional[str] = None
    bitrate_kbps: Optional[int] = None

# Endpoints
@app.post("/api/config/ip")
async def set_ip(req: IPConfigRequest):
    try:
        await state.initialize(req.ip)
        GLOBAL_CONFIG["camera_ip"] = req.ip
        return {"status": "ok", "ip": req.ip}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/config/ip")
async def get_ip():
    return {"ip": GLOBAL_CONFIG["camera_ip"], "connected": state.is_connected}

@app.post("/api/gimbal/rotate")
async def rotate(req: RotateRequest):
    if not state.client:
        raise HTTPException(status_code=503, detail="Camera not connected")
    try:
        await state.client.rotate(req.yaw, req.pitch)
    except TimeoutError:
        # High-frequency commands often timeout under load; ignore to keep logs clean
        pass
    except Exception as e:
        logger.warning(f"Rotate command failed: {e}")
    return {"status": "ok"}

@app.post("/api/gimbal/center")
async def center():
    if not state.client:
        raise HTTPException(status_code=503, detail="Camera not connected")
    try:
        await state.client.one_key_centering(CenteringAction.ONE_KEY_CENTER)
    except Exception as e:
        logger.error(f"Center command failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    return {"status": "ok"}

@app.post("/api/camera/photo")
async def take_photo():
    if not state.client:
        raise HTTPException(status_code=503, detail="Camera not connected")
    try:
        await state.client.capture(CaptureFuncType.PHOTO)
    except Exception as e:
        logger.error(f"Photo command failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    return {"status": "ok"}

@app.post("/api/camera/record")
async def toggle_record():
    if not state.client:
        raise HTTPException(status_code=503, detail="Camera not connected")
    try:
        await state.client.capture(CaptureFuncType.START_RECORD)
    except Exception as e:
        logger.error(f"Record command failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    return {"status": "ok"}

@app.post("/api/camera/zoom")
async def zoom(direction: int): # -1, 0, 1
    if not state.client:
        raise HTTPException(status_code=503, detail="Camera not connected")
    try:
        await state.client.manual_zoom(direction)
    except Exception as e:
        logger.warning(f"Zoom command failed: {e}")
    return {"status": "ok"}

@app.post("/api/camera/focus")
async def focus(direction: int): # -1, 0, 1
    if not state.client:
        raise HTTPException(status_code=503, detail="Camera not connected")
    try:
        await state.client.manual_focus(direction)
    except Exception as e:
        logger.warning(f"Focus command failed: {e}")
    return {"status": "ok"}

@app.get("/api/camera/encoding")
async def get_encoding():
    if not state.is_connected or not state.client:
        raise HTTPException(status_code=503, detail="Camera not connected")
    try:
        params = await state.client.get_encoding_params(StreamType.MAIN)
        return {
            "stream_type": params.stream_type.name,
            "enc_type": params.enc_type.name,
            "resolution": f"{params.resolution_w}x{params.resolution_h}",
            "bitrate_kbps": params.bitrate_kbps,
            "frame_rate": params.frame_rate
        }
    except Exception as e:
        logger.warning(f"Failed to get encoding params: {e}")
        raise HTTPException(status_code=503, detail="Failed to communicate with camera")

@app.post("/api/camera/encoding")
async def set_encoding(req: EncodingRequest):
    if not state.client:
        raise HTTPException(status_code=503, detail="Camera not connected")
    
    try:
        # Get current params to preserve other fields
        curr = await state.client.get_encoding_params(StreamType.MAIN)
        
        target_w, target_h = curr.resolution_w, curr.resolution_h
        if req.resolution:
            parts = req.resolution.split('x')
            if len(parts) == 2:
                target_w = int(parts[0])
                target_h = int(parts[1])
        
        logger.info(f"Setting encoding params: {target_w}x{target_h}, {req.bitrate_kbps or curr.bitrate_kbps} kbps")
        from siyi_sdk.models import EncodingParams
        params = EncodingParams(
            stream_type=curr.stream_type,
            enc_type=curr.enc_type,
            resolution_w=target_w,
            resolution_h=target_h,
            bitrate_kbps=req.bitrate_kbps or curr.bitrate_kbps,
            frame_rate=curr.frame_rate
        )
        
        success = await state.client.set_encoding_params(params)
        logger.info(f"Set encoding status: {success}")
        
        if success:
            # Restart stream in background as it might take a moment
            asyncio.create_task(state.restart_stream())
            
        return {"status": "ok" if success else "failed"}
    except Exception as e:
        logger.error(f"Set encoding failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/storage/format")
async def format_sd():
    if not state.is_connected or not state.client:
        raise HTTPException(status_code=503, detail="Camera not connected")
    try:
        success = await state.client.format_sd_card()
        return {"status": "ok" if success else "failed"}
    except TimeoutError as e:
        # Some cameras (ZT30/A8) do not ACK format commands despite succeeding.
        logger.warning(f"Format SD timed out, but command was likely received: {e}")
        return {"status": "ok", "warning": "timeout"}
    except Exception as e:
        logger.error(f"Format SD failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

class RebootRequest(BaseModel):
    camera: bool = False
    gimbal: bool = False

@app.post("/api/system/reboot")
async def reboot_system(req: RebootRequest):
    if not state.is_connected or not state.client:
        raise HTTPException(status_code=503, detail="Camera not connected")
    try:
        cam_ok, gim_ok = await state.client.soft_reboot(camera=req.camera, gimbal=req.gimbal)
        return {"status": "ok", "camera": cam_ok, "gimbal": gim_ok}
    except Exception as e:
        logger.error(f"Reboot failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/system/info")
async def get_system_info():
    if not state.is_connected or not state.client:
        raise HTTPException(status_code=503, detail="Camera not connected")
    try:
        hw_id = await state.client.get_hardware_id()
        fw = await state.client.get_firmware_version()
        
        return {
            "camera_type": hw_id.product_id.label,
            "camera_fw": FirmwareVersion.format_word(fw.camera),
            "gimbal_fw": FirmwareVersion.format_word(fw.gimbal),
            "zoom_fw": FirmwareVersion.format_word(fw.zoom)
        }
    except Exception as e:
        logger.warning(f"Failed to get system info: {e}")
        raise HTTPException(status_code=503, detail="Failed to communicate with camera")

@app.get("/api/media/directories")
async def list_dirs(type: int = 0):
    if not state.is_connected or not state.media:
        raise HTTPException(status_code=503, detail="Camera not connected")
    try:
        dirs = await state.media.list_directories(MediaType(type))
        return [{"name": d.name, "path": d.path} for d in dirs]
    except Exception as e:
        logger.error(f"List directories failed: {e}")
        raise HTTPException(status_code=503, detail="Media API unreachable")

@app.get("/api/media/files")
async def list_files(path: str, type: int = 0):
    if not state.is_connected or not state.media:
        raise HTTPException(status_code=503, detail="Camera not connected")
    try:
        files = await state.media.list_files(MediaType(type), path)
        return [{"name": f.name, "url": f.url} for f in files]
    except Exception as e:
        logger.error(f"List files failed: {e}")
        raise HTTPException(status_code=503, detail="Media API unreachable")

@app.get("/api/media/download")
async def download_media(url: str):
    import urllib.request
    import os
    try:
        # Extract filename from URL
        filename = os.path.basename(url.split('?')[0])
        
        # We proxy the download to force 'attachment' disposition
        # so the browser triggers a download dialog instead of playing it.
        def iter_file():
            with urllib.request.urlopen(url, timeout=10) as resp:
                while True:
                    chunk = resp.read(64 * 1024)
                    if not chunk:
                        break
                    yield chunk
        
        return StreamingResponse(
            iter_file(), 
            media_type="application/octet-stream",
            headers={"Content-Disposition": f"attachment; filename=\"{filename}\""}
        )
    except Exception as e:
        logger.error(f"Download proxy failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/stream/toggle")
async def toggle_stream(enabled: bool):
    try:
        await state.toggle_stream(enabled)
        return {"status": "ok", "enabled": enabled}
    except Exception as e:
        logger.error(f"Toggle stream failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.websocket("/ws/attitude")
async def websocket_attitude(websocket: WebSocket):
    await websocket.accept()
    try:
        while not state.stop_event.is_set():
            await websocket.send_json(state.attitude)
            await asyncio.sleep(0.1) # 10Hz
    except WebSocketDisconnect:
        pass

async def mjpeg_generator(request: Request) -> AsyncGenerator[bytes, None]:
    while not state.stop_event.is_set():
        if await request.is_disconnected():
            logger.debug("MJPEG client disconnected")
            break
        try:
            # Wait for frame with timeout to prevent hanging on reboot
            await asyncio.wait_for(state.frame_event.wait(), timeout=1.0)
            state.frame_event.clear()
            if state.latest_frame:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + state.latest_frame + b'\r\n')
        except asyncio.TimeoutError:
            # Just loop again and check stop_event and is_disconnected
            continue
        await asyncio.sleep(0.01)

@app.get("/api/stream/video")
async def video_stream(request: Request):
    return StreamingResponse(mjpeg_generator(request), media_type='multipart/x-mixed-replace; boundary=frame')

# Serve Static Files
UI_DIR = os.path.dirname(__file__)
STATIC_DIR = os.path.join(UI_DIR, "static")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/", response_class=HTMLResponse)
async def index():
    with open(os.path.join(UI_DIR, "index.html")) as f:
        return f.read()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=GLOBAL_CONFIG["port"])
