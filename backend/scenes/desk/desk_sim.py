import asyncio
import aiohttp
import json
import logging
from datetime import datetime
import numpy as np
from fastapi import WebSocket, WebSocketDisconnect

from utils.utils import (
    encode_numpy_array,
    send_personal_message,
)
from scenes.scene_abstract import SceneAbstract
from scenes.desk.desk_env import BeatTheDeskEnv

logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)


class BeatTheDeskSim(SceneAbstract):
    def __init__(self, objects) -> None:
        super().__init__()
        self.env = BeatTheDeskEnv(objects)
        self.objects = objects
        self.transform_objs()
        self.path = []

    def get_cubes_locations(self):
        return_list = []
        for obj in self.env.cubes:
            obj_ = {}
            obj_[list(obj.keys())[0]] = [
                int(float(x) * 100)
                for x in list(list(obj.values())[0].get_pos().cpu().numpy())
            ]
            obj_[list(obj.keys())[0]][2] += 3
            return_list.append(obj_)
        return return_list

    async def server_processor(
        self,
        message_queue: asyncio.Queue,
        actions_queue: asyncio.Queue,
        client_id: str,
        websocket: WebSocket,
    ):
        try:
            zoom = 0
            macro = 0

            cam_pos = self.env.cam.pos
            arm_pos = self.env.init_arm_dofs
            finger_pos = self.env.init_finger_dofs
            finger_grasp = False

            prev_qpos = [*arm_pos, *finger_pos]
            curr_qpos = [*arm_pos, *finger_pos]

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

                    if not actions_queue.empty():
                        action = np.array(await actions_queue.get())
                        print("action: ", action)

                        target = action[0:3] / 100
                        target[2] += 0.15
                        print("target: ", target)

                        prev_qpos = curr_qpos
                        curr_qpos = self.env.ik(curr_qpos, target)

                        if macro == 0 or macro == 4:
                            paths = self.env.path_to(prev_qpos, curr_qpos, 150)
                            for path in paths:
                                self.path.append((path, action[6]))
                        else:
                            self.path.extend([(curr_qpos, action[6])] * 100)

                        if macro == 6:
                            macro = 0
                            prev_qpos = curr_qpos
                            target[2] = 0.5
                            curr_qpos = self.env.ik(curr_qpos, target)
                            paths = self.env.path_to(prev_qpos, curr_qpos, 50)
                            for path in paths:
                                self.path.append((path, action[6]))
                        else:
                            macro += 1

                    if len(self.path) > 0:
                        path = self.path.pop(0)
                        arm_pos = path[0][:-2]
                        finger_grasp = False if path[1] == 1 else True

                    self.env.robot.control_dofs_position(
                        arm_pos,
                        self.env.arm_dofs_idx,
                    )

                    if finger_grasp:
                        self.env.grasp(True)
                    else:
                        self.env.grasp(False)

                    self.env.step()

                    lookat = np.array(self.env.cam.lookat)
                    self.env.cam.set_pose(
                        pos=cam_pos + zoom * (cam_pos - lookat),
                    )
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
        last_activity: datetime,
    ):
        try:
            while True:
                # Wait for message from client
                data = await websocket.receive_text()

                logger.info(data)

                try:
                    message_data = json.loads(data)
                except json.JSONDecodeError:
                    message_data = {"type": "message", "content": data}

                if message_data.get("type") == "command":
                    try:
                        async with aiohttp.ClientSession() as session:
                            robot_task_data = {
                                "instruction": message_data["content"],
                                "objects": self.get_cubes_locations(),
                            }

                            print(robot_task_data)

                            async with session.post(
                                "http://10.200.20.109:3348/robot/task",
                                headers={"Content-Type": "application/json"},
                                json=robot_task_data,
                            ) as response:
                                if response.status == 200:
                                    response_data = await response.json()
                                    logger.info(f"Robot task response: {response_data}")
                                    for action in response_data["actions"]:
                                        await actions_queue.put(action)

                                    await send_personal_message(
                                        websocket,
                                        json.dumps(
                                            {
                                                "type": "reasoning",
                                                "message": response_data["raw_output"],
                                            }
                                        ),
                                        client_id,
                                    )
                                else:
                                    logger.error(
                                        f"Robot task request failed with status {response.status}"
                                    )
                    except Exception as e:
                        logger.error(f"Error making robot task request: {str(e)}")

                else:
                    await message_queue.put(message_data)

        except WebSocketDisconnect:
            logger.info(f"Client {client_id} disconnected")
            raise
        except asyncio.CancelledError:
            logger.info(f"Client handler for client {client_id} cancelled")
        except Exception as e:
            logger.error(f"Client handler error for client {client_id}: {str(e)}")
            raise

    def transform_objs(self):
        new_objs = []
        for obj in self.objects:
            for k, v in obj.items():
                tmp = v
                tmp[0] = int(tmp[0] * 100)
                tmp[1] = int(tmp[1] * 100)
                tmp[2] = int(tmp[1] * 100)
                new_objs.append({k: tmp})

        self.objects = new_objs
