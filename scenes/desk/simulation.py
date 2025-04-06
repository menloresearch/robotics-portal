import asyncio
import aiohttp
import numpy as np
from fastapi import WebSocket, WebSocketDisconnect

from package.src.portal.utils.utils import (
    encode_numpy_array,
)
from scenes.desk.scene import Scene


class Simulation:
    def __init__(self, res) -> None:
        super().__init__()
        self.scene = Scene(res)
        self.path = []
        self.res = res
        self.actions_queue = []

    # TODO: Abstract to util or something else
    def get_cubes_locations(self):
        return_list = []
        for obj in self.scene.cubes:
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
        websocket: WebSocket,
    ):
        try:
            zoom = 0
            macro = 0

            cam_pos = self.scene.cam_main.pos
            arm_pos = self.scene.init_arm_dofs

            finger_pos = self.scene.init_finger_dofs
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

                    if message.get("type") == "zoom":
                        if message["direction"] == "in":
                            if zoom > -0.8:
                                zoom -= 0.1
                        elif message["direction"] == "out":
                            if zoom < 1:
                                zoom += 0.1

                    elif message.get("type") == "resolution_change":
                        self.res = message.get("resolution")
                        if self.res == 1080:
                            self.scene.cam_main = self.scene.cam_1080
                        elif self.res == 720:
                            self.scene.cam_main = self.scene.cam_720
                        elif self.res == 480:
                            self.scene.cam_main = self.scene.cam_480

                    # elif message.get("type") == "stop":
                    #     while not actions_queue.empty():
                    #         actions_queue.get_nowait()
                    #         actions_queue.task_done()

                    if not len(self.actions_queue) == 0:
                        action = np.array(self.actions_queue.pop(0))
                        print("action: ", action)

                        target = action[0:3] / 100
                        target[2] += 0.15
                        print("target: ", target)

                        prev_qpos = curr_qpos
                        curr_qpos = self.scene.ik(curr_qpos, target)

                        if macro == 0 or macro == 4:
                            paths = self.scene.path_to(prev_qpos, curr_qpos, 150)
                            for path in paths:
                                self.path.append((path, action[6]))
                        else:
                            self.path.extend([(curr_qpos, action[6])] * 100)

                        if macro == 6:
                            macro = 0
                            prev_qpos = curr_qpos
                            target[2] = 0.5
                            curr_qpos = self.scene.ik(curr_qpos, target)
                            paths = self.scene.path_to(prev_qpos, curr_qpos, 50)
                            for path in paths:
                                self.path.append((path, action[6]))
                        else:
                            macro += 1

                    if len(self.path) > 0:
                        path = self.path.pop(0)
                        arm_pos = path[0][:-2]
                        finger_grasp = False if path[1] == 1 else True

                    self.scene.robot.control_dofs_position(
                        arm_pos,
                        self.scene.arm_dofs_idx,
                    )

                    if finger_grasp:
                        self.scene.grasp(True)
                    else:
                        self.scene.grasp(False)

                    self.scene.step()

                    lookat = np.array(self.scene.cam_main.lookat)
                    self.scene.cam_main.set_pose(
                        pos=cam_pos + zoom * (cam_pos - lookat),
                    )
                    main_view, _, _, _ = self.scene.cam_main.render()
                    secondary_view, _, _, _ = self.scene.cam_secondary.render()

                    processed_message = {
                        "type": "streaming_view",
                        "main_view": encode_numpy_array(main_view),
                        "god_view": encode_numpy_array(secondary_view),
                    }

                    await websocket.send_json(processed_message)
                    await asyncio.sleep(0.001)

                except WebSocketDisconnect:
                    # logger.error("Websocket disconnected")
                    raise
                except Exception as e:
                    # logger.error(f"Error while rendering: {str(e)}")
                    await websocket.send_json(
                        {
                            "type": "error",
                            "message": f"Error while rendering: {str(e)}",
                        }
                    )
                    raise

        except asyncio.CancelledError:
            # logger.error(f"Server processor for client {client_id} cancelled")
            return
        except Exception:
            # logger.error(f"Server processor error for client {client_id}: {str(e)}")
            return

    async def client_handler(
        self,
        message_queue: asyncio.Queue,
        websocket: WebSocket,
    ):
        try:
            while True:
                # Wait for message from client
                message = await websocket.receive_json()

                if message.get("type") == "command":
                    try:
                        async with aiohttp.ClientSession() as session:
                            robot_task_data = {
                                "instruction": message["content"],
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
                                    # logger.info(f"Robot task response: {response_data}")
                                    for action in response_data["actions"]:
                                        self.actions_queue.append(action)
                                        pass

                                    await websocket.send_json(
                                        {
                                            "type": "reasoning",
                                            "message": response_data["raw_output"],
                                        }
                                    )
                                else:
                                    await websocket.send_json(
                                        {
                                            "type": "reasoning",
                                            "message": f"Fail with status {response.status}",
                                        }
                                    )
                    except Exception:
                        raise

                else:
                    await message_queue.put(message)

        except WebSocketDisconnect:
            # logger.info(f"Client {client_id} disconnected")
            return
        except asyncio.CancelledError:
            # logger.info(f"Client handler for client {client_id} cancelled")
            return
        except Exception:
            # logger.error(f"Client handler error for client {client_id}: {str(e)}")
            return
