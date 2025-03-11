from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import json
import uvicorn
import asyncio
import logging
import torch
import genesis as gs
from screnes.go2.go2_env import Go2Env
from utils.utils import send_personal_message
import os
from contextlib import asynccontextmanager
import pickle
from rsl_rl.runners import OnPolicyRunner
from utils.utils import encode_numpy_array, send_openai_request, parse_json_from_mixed_string
import random
import numpy as np
from dotenv import load_dotenv
from screnes.go2.go2_sim import Go2Sim
# Set up logging
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load the ML mode
    gs.init()
    load_dotenv()
    yield
    # Clean up the ML models and release the resources


app = FastAPI(lifespan=lifespan, title="Fully Self-Contained WebSocket Server")

# Regular HTTP endpoint


@app.get("/")
async def get():
    return {"message": "WebSocket server is running. Connect to /ws to use WebSocket."}


# WebSocket endpoint with no external dependencies


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    # Static variable to keep track of all active connections
    # Using class attribute pattern to avoid global variables
    # if not hasattr(websocket_endpoint, "active_connections"):

    
    active_connections = {}
    
    # Accept connection
    await websocket.accept()
    client_id = id(websocket)
    active_connections[client_id] = websocket

    logger.info(
        f"Client {client_id} connected. Total clients: {len(active_connections)}"
    )

    # Create message queue local to this websocket connection
    message_queue = asyncio.Queue()
    actions_queue = asyncio.Queue()

    # Helper functions for WebSocket communication

    # Notify about new connection
    await send_personal_message(websocket,
        json.dumps({"type": "connection_established, initalizing ...", "client_id": client_id}),
        client_id,
    )
    go2_sim = Go2Sim()

    
    # Run both coroutines concurrently
    server_task = asyncio.create_task(go2_sim.server_processor(message_queue, actions_queue, client_id, websocket))
    client_task = asyncio.create_task(go2_sim.client_handler(message_queue, actions_queue, client_id, websocket))

    try:
        # Wait for either task to finish (usually due to disconnect)
        done, pending = await asyncio.wait(
            [server_task, client_task], return_when=asyncio.FIRST_COMPLETED
        )

        # Cancel the remaining task
        for task in pending:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

    except Exception as e:
        logger.error(f"WebSocket error for client {client_id}: {str(e)}")
    finally:
        # Clean up - remove connection from active connections
        if client_id in active_connections:
            del active_connections[client_id]

        # Log remaining clients
        logger.info(
            f"Client {client_id} removed. Remaining clients: {len(active_connections)}"
        )

        # Notify about disconnection (optional)


if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=False)
