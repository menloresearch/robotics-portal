import asyncio
import json
import logging
import numpy as np
import cv2
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from typing import Dict, List
import time

from sim import render_cam

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Add CORS middleware to allow frontend connections
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Store active connections
active_connections: List[WebSocket] = []


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)

    # Default settings
    target_fps = 30
    frame_time = 1.0 / target_fps
    cam_id = 0
    steps = 0
    zoom = 0
    pan = [0, 0, 0]

    try:
        while True:
            # Check for any incoming messages (e.g., FPS changes)
            try:
                data = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=0.001,  # Small timeout to not block the stream
                )
                message = json.loads(data)
                if message.get("type") == "fps_change":
                    new_fps = float(message["fps"])
                    # Clamp FPS between reasonable values
                    target_fps = max(1, min(new_fps, 60))
                    frame_time = 1.0 / target_fps
                    logger.info(f"FPS changed to {target_fps}")

                if message.get("type") == "camera_change":
                    cam_id = int(message["camera"])
                    logger.info(f"Camera changed to {cam_id}")

                if message.get("type") == "zoom":
                    if message["direction"] == "in":
                        if zoom > -0.8:
                            zoom -= 0.1
                    elif message["direction"] == "out":
                        if zoom < 1:
                            zoom += 0.1

                if message.get("type") == "pan":
                    pan = message["delta"]

            except asyncio.TimeoutError:
                pass  # No message received, continue streaming

            # Stream the frame
            start_time = time.time()

            def_pos = np.array([3.5, 0.0, 2.5])
            frame, steps, def_pos = render_cam(cam_id, steps, zoom, pan, def_pos)
            pan = [0, 0, 0]

            # Convert numpy array to JPEG
            success, encoded_frame = cv2.imencode(".jpg", frame)
            if not success:
                logger.error("Failed to encode frame")
                continue

            # Send the frame
            await websocket.send_bytes(encoded_frame.tobytes())

            # Maintain frame rate
            elapsed = time.time() - start_time
            sleep_time = max(0, frame_time - elapsed)
            await asyncio.sleep(sleep_time)

    except WebSocketDisconnect:
        logger.info("Client disconnected")
        active_connections.remove(websocket)
    except Exception as e:
        logger.error(f"Error in WebSocket connection: {e}")
        if websocket in active_connections:
            active_connections.remove(websocket)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True, log_level="info")
