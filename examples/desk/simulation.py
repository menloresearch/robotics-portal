import asyncio
import aiohttp
import numpy as np
from fastapi import WebSocket, WebSocketDisconnect

from portal.utils import encode_numpy_array
from .scene import Scene


class Simulation:
    def __init__(self, res) -> None:
        super().__init__()
        self.res = res
        self.scene = Scene(res)

        self.init_cam_pos = self.scene.cam_main.pos
        self.zoom = 0  # View zoom

        self.actions_queue = []  # Processed actions from message is added here
        self.path = []
        self.prev_qpos = [*self.scene.init_arm_dofs, *self.scene.init_finger_dofs]
        self.curr_qpos = [*self.scene.init_arm_dofs, *self.scene.init_finger_dofs]
        self.arm_pos = self.scene.init_arm_dofs
        self.finger_grasp = False
        self.macro = 0

    async def server_processor(
        self,
        websocket: WebSocket,
    ):
        try:
            while True:
                if not len(self.actions_queue) == 0:
                    action = np.array(self.actions_queue.pop(0))
                    print("action: ", action)

                    # Model use 100 x 100, Sim use 1 x 1 in term of unit
                    target = action[0:3] / 100
                    target[2] += 0.15  # Pad the height of the gripper
                    print("target: ", target)

                    self.prev_qpos = self.curr_qpos
                    self.curr_qpos = self.scene.ik(self.curr_qpos, target)

                    if self.macro == 0 or self.macro == 4:
                        paths = self.scene.path_to(self.prev_qpos, self.curr_qpos, 150)
                        for path in paths:
                            self.path.append((path, action[6]))
                    else:
                        self.path.extend([(self.curr_qpos, action[6])] * 100)

                    if self.macro == 6:  # AI model returned 7 actions
                        self.macro = 0
                        self.prev_qpos = self.curr_qpos
                        target[2] = 0.5
                        self.curr_qpos = self.scene.ik(self.curr_qpos, target)
                        paths = self.scene.path_to(self.prev_qpos, self.curr_qpos, 50)
                        for path in paths:
                            self.path.append((path, action[6]))
                    else:
                        self.macro += 1

                if len(self.path) > 0:
                    path = self.path.pop(0)
                    self.arm_pos = path[0][:-2]
                    self.finger_grasp = False if path[1] == 1 else True

                self.scene.robot.control_dofs_position(
                    self.arm_pos,
                    self.scene.arm_dofs_idx,
                )

                if self.finger_grasp:
                    self.scene.grasp(True)
                else:
                    self.scene.grasp(False)

                self.scene.step()
                main_view, secondary_view = self.update_camera()

                await websocket.send_json(
                    {
                        "type": "streaming_view",
                        "main_view": main_view,
                        "god_view": secondary_view,
                    }
                )
                await asyncio.sleep(0.001)

        except WebSocketDisconnect:
            raise Exception("Websocket discconected")
        except asyncio.CancelledError:
            raise Exception("Asyncio cancelled")
        except Exception as e:
            raise Exception(f"Exception occured: {e}")

    def update_camera(self):
        lookat = self.scene.cam_main.lookat

        self.scene.cam_main.set_pose(
            pos=self.init_cam_pos + self.zoom * (self.init_cam_pos - lookat),
        )
        main_view, _, _, _ = self.scene.cam_main.render()
        secondary_view, _, _, _ = self.scene.cam_secondary.render()

        return encode_numpy_array(main_view), encode_numpy_array(secondary_view)

    async def client_handler(
        self,
        websocket: WebSocket,
    ):
        try:
            while True:
                message = await websocket.receive_json()

                if message.get("type") == "command":
                    await self.get_model_reasoning(websocket, message)

                if message.get("type") == "zoom":
                    if message["direction"] == "in":
                        if self.zoom > -0.8:
                            self.zoom -= 0.1
                    elif message["direction"] == "out":
                        if self.zoom < 1:
                            self.zoom += 0.1

                if message.get("type") == "resolution_change":
                    self.res = message.get("resolution")
                    if self.res == 1080:
                        self.scene.cam_main = self.scene.cam_1080
                    elif self.res == 720:
                        self.scene.cam_main = self.scene.cam_720
                    elif self.res == 480:
                        self.scene.cam_main = self.scene.cam_480

        except WebSocketDisconnect:
            raise Exception("Websocket discconected")
        except asyncio.CancelledError:
            raise Exception("Asyncio cancelled")
        except Exception as e:
            raise Exception(f"Exception occured: {e}")
        finally:
            # clean up actions state
            self.actions_queue = []

    async def get_model_reasoning(self, websocket, message):
        robot_task_data = {
            "instruction": message["content"],
            "objects": self.scene.get_cubes_locations(),
        }

        try:
            async with aiohttp.ClientSession() as session:
                print(robot_task_data)

                async with session.post(
                    "http://10.200.20.109:3348/robot/task",
                    # "https://alphaspace.menlo.ai/api",
                    headers={"Content-Type": "application/json"},
                    json=robot_task_data,
                ) as response:
                    if response.status == 200:
                        response_data = await response.json()
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
        except Exception as e:
            raise Exception(f"Exception occured: {e}")
