from fastapi import FastAPI, WebSocket
import json
import uvicorn
import asyncio
from datetime import datetime
import logging
import genesis as gs
from utils.utils import send_personal_message, check_timeout
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from scenes.go2.go2_sim import Go2Sim
from scenes.g1_mall.g1_sim import G1Sim
from scenes.desk.desk_sim import BeatTheDeskSim

import os

os.environ["CUDA_VISIBLE_DEVICES"] = "0"

# Set up logging
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    load_dotenv()
    yield


app = FastAPI(lifespan=lifespan, title="Fully Self-Contained WebSocket Server")


# Regular HTTP endpoint
@app.get("/")
async def get():
    return {"message": "WebSocket server is running. Connect to /ws to use WebSocket."}


@app.get("/defaul-scene-config")
def default_config():
    return json.load(open("assets/default_scene_configuration.json", "r"))


# WebSocket endpoint with no external dependencies


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    # BUG: reconnecting will create intialisation error
    if not gs._initialized:
        gs.init()

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

    # Notify about new connection
    await send_personal_message(
        websocket,
        json.dumps({"type": "connection_established", "client_id": client_id}),
        client_id,
    )

    # Will only advance after receiving text for environment from websocket
    while True:
        data = await websocket.receive_text()
        message_data = json.loads(data)

        objects_stack = [
            {"red-cube": []},
            {"black-cube": []},
            {"green-cube": []},
            {"purple-cube": []},
        ]

        objects_place = [
            {"red-cube": []},
            {"black-cube": []},
            {"green-container": []},
        ]

        if message_data.get("type") == "env":
            if message_data.get("env") == "go2":
                scene = Go2Sim(
                    config=message_data.get(
                        "config", default_config()["scenes"].get("go2", {})
                    )
                )

            elif message_data.get("env") == "g1":
                scene = G1Sim(
                    config=message_data.get(
                        "config", default_config()["scenes"].get("g1", {})
                    )
                )

            elif message_data.get("env") == "arm-stack":
                objects = message_data.get("positions")
                i = 0
                for v in objects.values():
                    if i < len(objects_stack):
                        for key in objects_stack[i].keys():
                            objects_stack[i][key] = v
                        i += 1
                print(objects_stack)

                scene = BeatTheDeskSim(objects_stack)

            elif message_data.get("env") == "arm-place":
                objects = message_data.get("positions")
                i = 0
                for v in objects.values():
                    if i < len(objects_place):
                        for key in objects_place[i].keys():
                            objects_place[i][key] = v
                        i += 1
                print(objects_place)

                scene = BeatTheDeskSim(objects_place)

            break

    await send_personal_message(
        websocket,
        json.dumps({"type": "initialized", "client_id": client_id}),
        client_id,
    )
    last_activity = datetime.now()

    # Run both coroutines concurrently
    server_task = asyncio.create_task(
        scene.server_processor(message_queue, actions_queue, client_id, websocket)
    )
    client_task = asyncio.create_task(
        scene.client_handler(
            message_queue, actions_queue, client_id, websocket, last_activity
        )
    )

    timeout_task = asyncio.create_task(check_timeout(websocket, last_activity))

    try:
        # Wait for either task to finish (usually due to disconnect)
        done, pending = await asyncio.wait(
            [server_task, client_task, timeout_task],
            return_when=asyncio.FIRST_COMPLETED,
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
        logger.error(
            f"Client {client_id} removed. Remaining clients: {len(active_connections)}"
        )

    gs.destroy()


if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=False)
