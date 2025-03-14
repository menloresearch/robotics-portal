import asyncio
import json
import logging

from fastapi import WebSocket, WebSocketDisconnect
from scenes.scene_abstract import SceneAbstract
from utils.utils import (
    encode_numpy_array,
    send_personal_message,
)

from scenes.desk.desk_env import BeatTheDeskEnv

logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)


class BeatTheDeskSim(SceneAbstract):
    def __init__(self) -> None:
        super().__init__()
        self.env = BeatTheDeskEnv()

    async def server_processor(
        self,
        message_queue: asyncio.Queue,
        actions_queue: asyncio.Queue,
        client_id: str,
        websocket: WebSocket,
    ):
        zoom = 0

        try:
            steps = 100
            step = 0

            while True:
                try:
                    # Get message from queue (added by client handler)
                    if not message_queue.empty():
                        message = await message_queue.get()
                    else:
                        message = {}

                    # Process the message (server-side logic)
                    logger.info(
                        f"Processing message from client {client_id}: {message}"
                    )

                    # Example: Add some server-side processing
                    if message.get("type") == "zoom":
                        if message["direction"] == "in":
                            if zoom > -0.8:
                                zoom -= 0.1
                        elif message["direction"] == "out":
                            if zoom < 1:
                                zoom += 0.1

                    elif message.get("type") == "stop":
                        while not actions_queue.empty():
                            actions_queue.get_nowait()
                            actions_queue.task_done()

                    if step < steps:
                        step += 1

                        main_view, _, _, _ = self.env.cam.render()
                        god_view, _, _, _ = self.env.cam_god.render()

                        main_view = main_view[:, :, ::-1]
                        god_view = god_view[:, :, ::-1]

                        processed_message = {
                            "type": "streaming_view",
                            "main_view": encode_numpy_array(main_view),
                            "god_view": encode_numpy_array(god_view),
                        }

                        await send_personal_message(
                            websocket, json.dumps(processed_message), client_id
                        )
                        await asyncio.sleep(0.001)

                    else:
                        step = 0
                except WebSocketDisconnect:
                    logger.error("Websocket disconnected")
                    return
                except Exception as e:
                    logger.error(f"Error while rendering: {str(e)}")
                    await send_personal_message(
                        websocket,
                        json.dumps(
                            {
                                "type": "error",
                                "message": f"Error while rendering: {str(e)}",
                            }
                        ),
                        client_id,
                    )
                    return

        except asyncio.CancelledError:
            logger.error(f"Server processor for client {client_id} cancelled")
            return
        except Exception as e:
            logger.error(f"Server processor error for client {client_id}: {str(e)}")
            return

    async def client_handler(
        self,
        message_queue: asyncio.Queue,
        actions_queue: asyncio.Queue,
        client_id: str,
        websocket: WebSocket,
    ):
        try:
            while True:
                # Wait for message from client
                data = await websocket.receive_text()

                try:
                    message_data = json.loads(data)
                except json.JSONDecodeError:
                    message_data = {"type": "message", "content": data}

        except WebSocketDisconnect:
            logger.info(f"Client {client_id} disconnected")
            raise
        except asyncio.CancelledError:
            logger.info(f"Client handler for client {client_id} cancelled")
        except Exception as e:
            logger.error(f"Client handler error for client {client_id}: {str(e)}")
            raise
