import numpy as np
import os
from fastapi import WebSocket, WebSocketDisconnect
import asyncio
import json
import torch
import pickle
from scenes.scene_abstract import SceneAbstract
from scenes.go2.go2_env import Go2Env
from rsl_rl.runners import OnPolicyRunner
from datetime import datetime
from utils.utils import (
    encode_numpy_array,
    send_personal_message,
    send_openai_request,
    parse_json_from_mixed_string,
    SYSTEM_PROMPT
)
from config import Config
import logging

logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)


class Go2Sim(SceneAbstract):
    def __init__(self, config={}):
        super().__init__()
        self.dir_path = os.path.dirname(os.path.realpath(__file__))
        self.load_policy(config)
        self.config = config

    def load_policy(self, config):
        model_config = config.get("models", {}).get("rl", {})
        # global policy_walk, policy_stand, policy_right, policy_left, env
        log_dir = model_config.get(
            "walking", "scenes/go2/checkpoints/go2-walking")
        env_cfg, obs_cfg, reward_cfg, command_cfg, train_cfg = pickle.load(
            open(log_dir+"/cfgs.pkl", "rb")
        )
        reward_cfg["reward_scales"] = {}

        self.env = Go2Env(
            num_envs=1,
            env_cfg=env_cfg,
            obs_cfg=obs_cfg,
            reward_cfg=reward_cfg,
            command_cfg=command_cfg,
            show_viewer=False,
            scene_config=config
        )

        runner = OnPolicyRunner(self.env, train_cfg, log_dir, device="cpu")
        resume_path = os.path.join(log_dir, "model_500.pt")
        runner.load(resume_path)
        self.policy_walk = runner.get_inference_policy(device="cuda:0")

        log_dir = model_config.get("left", "scenes/go2/checkpoints/go2-left")

        env_cfg, obs_cfg, reward_cfg, command_cfg, train_cfg = pickle.load(
            open(log_dir+"/cfgs.pkl", "rb")
        )
        reward_cfg["reward_scales"] = {}

        runner = OnPolicyRunner(self.env, train_cfg, log_dir, device="cpu")
        resume_path = os.path.join(log_dir, "model_500.pt")
        runner.load(resume_path)
        self.policy_left = runner.get_inference_policy(device="cuda:0")

        log_dir = model_config.get("right", "scenes/go2/checkpoints/go2-right")
        env_cfg, obs_cfg, reward_cfg, command_cfg, train_cfg = pickle.load(
            open(log_dir+"/cfgs.pkl", "rb")
        )
        reward_cfg["reward_scales"] = {}

        runner = OnPolicyRunner(self.env, train_cfg, log_dir, device="cpu")
        resume_path = os.path.join(log_dir, "model_500.pt")
        runner.load(resume_path)
        self.policy_right = runner.get_inference_policy(device="cuda:0")

        log_dir = model_config.get("stand", "scenes/go2/checkpoints/go2-stand")
        env_cfg, obs_cfg, reward_cfg, command_cfg, train_cfg = pickle.load(
            open(log_dir+"/cfgs.pkl", "rb")
        )
        reward_cfg["reward_scales"] = {}

        runner = OnPolicyRunner(self.env, train_cfg, log_dir, device="cpu")
        resume_path = os.path.join(log_dir, "model_500.pt")
        runner.load(resume_path)
        self.policy_stand = runner.get_inference_policy(device="cuda:0")
        self.list_actions = [
            self.policy_right,
            self.policy_left,
            self.policy_stand,
            self.policy_walk,
        ]
        return

    def transform(self, action, amplitude):
        if action == 0 or action == 1:  # right or left
            amplitude = amplitude * 75 / 45

        elif action == 3:
            amplitude = amplitude * 120
        return amplitude

    def apply_policy(self, policy, env, obs, num_steps=1000):
        # env.reset()
        for _ in range(num_steps):
            action = policy(obs)
            obs, _, rews, dones, infos = env.step(action)
        return obs

    async def server_processor(
        self,
        message_queue: asyncio.Queue,
        actions_queue: asyncio.Queue,
        client_id: str,
        websocket: WebSocket,
    ):
        actions_map = {
            "move_forward": 3,
            "rotate_left": 1,
            "rotate_right": 0,
            "wait": 2,
        }

        obs, _ = self.env.reset()
        main = 0
        zoom = 0
        try:
            steps = 100
            step = 0
            stop = True
            def_pos = self.env.cam_god.pos
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
                        stop = True
                        # erase the actions queue
                        while not actions_queue.empty():
                            actions_queue.get_nowait()
                            actions_queue.task_done()

                    elif message.get("type") == "camera_change":
                        main = message.get("camera")

                    if (not actions_queue.empty()) and stop == True:
                        action, amptitude = await actions_queue.get()
                        logger.info("action: " + str(action) +
                                    ", am:" + str(amptitude))
                        action = actions_map[action]
                        steps = self.transform(action, amptitude)
                        logger.info("action: " + str(action) +
                                    ", steps:" + str(steps))
                        step = 0
                        stop = False

                    # render image then send message to client

                    if step < steps:
                        step += 1

                        if main == 0:
                            main_view, _, _, _ = self.env.cam_first.render()
                        else:
                            main_view, _, _, _ = self.env.cam.render()

                        lookat = np.array(self.env.cam_god.lookat)
                        self.env.cam_god.set_pose(
                            pos=def_pos + zoom * (def_pos - lookat),
                        )
                        god_view, _, _, _ = self.env.cam_god.render()

                        main_view = main_view[:, :, ::-1]
                        god_view = god_view[:, :, ::-1]
                        with torch.no_grad():
                            if stop:
                                actions = self.list_actions[2](obs)  # stand
                                obs, _, rews, dones, infos = self.env.step(
                                    actions)
                            else:
                                actions = self.list_actions[action](obs)
                                obs, _, rews, dones, infos = self.env.step(
                                    actions)
                        processed_message = {
                            "type": "streaming_view",
                            "main_view": encode_numpy_array(main_view),
                            "god_view": encode_numpy_array(god_view),
                        }

                        await send_personal_message(
                            websocket, json.dumps(processed_message), client_id
                        )
                        # print("robot position:", env.position)
                        await asyncio.sleep(0.001)

                    else:
                        step = 0
                        stop = True
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
                # Mark task as done
                # message_queue.task_done()
        except asyncio.CancelledError:
            logger.error(f"Server processor for client {client_id} cancelled")
            return
        except Exception as e:
            logger.error(
                f"Server processor error for client {client_id}: {str(e)}")
            return

    async def client_handler(
        self,
        message_queue: asyncio.Queue,
        actions_queue: asyncio.Queue,
        client_id: str,
        websocket: WebSocket,
        last_activity: datetime,
    ):
        model_config = self.config.get("models", {}).get("llm", {})
        api_url = model_config.get("api_url", Config.openai_base_url)
        llm_model = model_config.get("model", Config.llm_model)
        api_key = model_config.get("api_key", Config.api_key)
        system_prompt = model_config.get("system_prompt", SYSTEM_PROMPT)
        try:
            while True:
                # Wait for message from client
                data = await websocket.receive_text()

                # Parse the message
                try:
                    message_data = json.loads(data)
                except json.JSONDecodeError:
                    message_data = {"type": "message", "content": data}

                # Add client message to processing queue
                if message_data.get("type") == "command":
                    final_answer = ""
                    content = message_data.get("content", "")
                    robot_position = str(self.env.position)
                    content += ". Robot is at the position " + robot_position
                    async for chunk in send_openai_request(api_url=api_url, api_key=api_key, system_prompt=system_prompt, prompt=content, model=llm_model):
                        await send_personal_message(
                            websocket,
                            json.dumps(
                                {
                                    "type": "reasoning",
                                    "message": chunk["choices"][0]["delta"].get(
                                        "content", ""
                                    ),
                                }
                            ),
                            client_id,
                        )

                        final_answer += chunk["choices"][0]["delta"].get(
                            "content", "")
                    actions = parse_json_from_mixed_string(final_answer)
                    print(final_answer)
                    if actions is None:
                        await send_personal_message(
                            websocket,
                            json.dumps(
                                {
                                    "type": "error",
                                    "message": "can not parse action from LLM",
                                }
                            ),
                            client_id,
                        )
                    else:
                        actions = actions["actions"]
                        for action in actions:
                            await actions_queue.put(
                                (
                                    action["type"],
                                    action.get(
                                        "angle", action.get("distance", 0)),
                                )
                            )

                        await send_personal_message(
                            websocket,
                            json.dumps(
                                {
                                    "type": "output",
                                    "message": actions,
                                }
                            ),
                            client_id,
                        )

                else:
                    await message_queue.put(message_data)
                last_activity = datetime.now()

        except WebSocketDisconnect:
            logger.info(f"Client {client_id} disconnected")
            raise
        except asyncio.CancelledError:
            logger.info(f"Client handler for client {client_id} cancelled")
        except Exception as e:
            logger.error(
                f"Client handler error for client {client_id}: {str(e)}")
            raise
