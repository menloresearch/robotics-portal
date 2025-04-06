import asyncio
import genesis as gs
import json
from typing import List
from fastapi import WebSocket, APIRouter


class WebSocketManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)


class Server:
    def __init__(self):
        self.router = APIRouter(tags=["websocket"])
        self.manager = WebSocketManager()
        self.scenes = [
            {"id": "default", "name": "Default"},
        ]
        self.sims = {}
        self.main_sim = None

        self.router.add_api_websocket_route("/ws", self.websocket_endpoint)

    def set_scenes(self, options):
        self.scenes = options
        return self.scenes

    def register_simulations(self, sims):
        if not isinstance(sims, list):
            sims = [sims]

        for sim in sims:
            self.sims[sim["id"]] = sim["sim"]

    async def websocket_endpoint(self, websocket: WebSocket):
        if not gs._initialized:
            gs.init()

        await self.manager.connect(websocket)
        message_queue = asyncio.Queue()

        # Sending back confirmation
        await websocket.send_json(
            {
                "type": "connection_established",
                "content": json.dumps({"scenes": self.scenes}),
            }
        )

        # Advance only when scene is chosen
        while True:
            try:
                message = await websocket.receive_json()

                if message.get("type") == "scene":
                    res = message.get("resolution")
                    scene = message.get("scene")
                    if scene in self.sims.keys():
                        self.main_sim = self.sims[scene](res)
                        break

            except Exception:
                raise

        # Run both coroutines concurrently
        server_task = asyncio.create_task(
            self.main_sim.server_processor(message_queue, websocket)
        )
        client_task = asyncio.create_task(
            self.main_sim.client_handler(message_queue, websocket)
        )

        try:
            # Wait for either task to finish (usually due to disconnect)
            done, pending = await asyncio.wait(
                [server_task, client_task],
                return_when=asyncio.FIRST_COMPLETED,
            )

            # Cancel the remaining task
            for task in pending:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

        except Exception:
            raise

        gs.destroy()
