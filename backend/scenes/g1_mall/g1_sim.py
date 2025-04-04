import numpy as np
import os
from fastapi import WebSocket, WebSocketDisconnect
import asyncio
import json
import torch
import pickle
from scenes.scene_abstract import SceneAbstract
from datetime import datetime
from scenes.g1_mall.g1_env import G1Env
from rsl_rl.runners import OnPolicyRunner
from utils.utils import (
    encode_numpy_array,
    send_personal_message,
    send_openai_request,
    parse_json_from_mixed_string,
    decode_base64_to_audio,
    encode_audio_to_base64,
    parse_action_robot_in_mall
)
from utils.system_prompt import SYSTEM_PROMPT, SYSTEM_PROMPT_WAREHOUSE
import logging
from config import Config
from services.LLMService import AsyncOpenAIChatCompletionService
from services.AudioService import AudioService

logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)


class G1SimMall(SceneAbstract):
    def __init__(self, config={}):
        super().__init__()
        self.dir_path = os.path.dirname(os.path.realpath(__file__))
        self.load_policy(config)
        self.config = config
        self.llm_service = AsyncOpenAIChatCompletionService(config=config)
        self.audio_service = AudioService(config=config)

    def load_policy(self, config):
        model_config = config.get("models", {}).get("rl", {})

        log_dir = model_config.get(
            "walking", "scenes/g1/checkpoints/g1-walking")
        env_cfg, obs_cfg, reward_cfg, command_cfg, train_cfg, domain_rand_cfg = pickle.load(
            open(log_dir+"/cfgs.pkl", "rb")
        )
        reward_cfg["reward_scales"] = {}

        self.env = G1Env(
            num_envs=1,
            env_cfg=env_cfg,
            obs_cfg=obs_cfg,
            reward_cfg=reward_cfg,
            command_cfg=command_cfg,
            domain_rand_cfg=domain_rand_cfg,
            show_viewer=False,
            scene_config=config
        )

        return

    def transform(self, action, amplitude):
        if action == 1:  # left
            amplitude = amplitude * 100 / 45
        elif action == 0:  # right
            amplitude = amplitude * 90 / 45
        elif action == 3:
            amplitude = amplitude * 120
        return amplitude

    def apply_policy(self, policy, env, obs, num_steps=1000):
        # env.reset()
        for _ in range(num_steps):
            action = policy(obs)
            obs, _, rews, dones, infos = env.step(action)
        return obs

    async def handle_voice_command(self, message_data: dict, websocket: WebSocket, client_id: str, actions_queue: asyncio.Queue):
        if message_data.get("content"):
            final_answer = ""
            audio_byte_input = decode_base64_to_audio(message_data["content"])
            content = await self.audio_service.stt(audio_data=audio_byte_input)
            robot_position = str(self.env.position)
            content += ". Robot is at the position " + robot_position
            async for chunk in self.llm_service.chat_completion_stream(message_content=content):
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
                chunk_content = chunk["choices"][0]["delta"].get("content", "")
                if chunk_content in "GOODBYE" and chunk_content != "":
                    await actions_queue.put(
                        "greeting"
                    )
                    await send_personal_message(
                        websocket,
                        json.dumps(
                            {
                                "type": "output",
                                "message": "greeting",
                                "signal": chunk_content
                            }
                        ),
                        client_id,
                    )
                    continue
                elif chunk_content in "UNKNOWN" and chunk_content != "":
                    await actions_queue.put("head_scratch")
                    await send_personal_message(
                        websocket,
                        json.dumps(
                            {
                                "type": "output",
                                "message": "head_scratch",
                                "signal": chunk_content
                            }
                        ),
                        client_id,
                    )
                    continue
                final_answer += chunk_content
                await self.audio_service.llm_text_queue.put(chunk)
                # self.audio_service.llm_text_queue.task_done()
            # send end signal
            await self.audio_service.llm_text_queue.put(None)
            # self.audio_service.llm_text_queue.task_done()
            actions = parse_action_robot_in_mall(final_answer)
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
                try:
                    actions = actions["actions"]
                    for action in actions:
                        await actions_queue.put(

                            action["type"]

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
                except Exception as e:
                    print(e)
                    pass

    async def handle_text_command(self, message_data: dict, websocket: WebSocket, client_id: str, actions_queue: asyncio.Queue):
        final_answer = ""
        content = message_data.get("content", "")
        robot_position = str(self.env.position)
        content += ". Robot is at the position " + robot_position
        async for chunk in self.llm_service.chat_completion_stream(message_content=content):
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
            chunk_content = chunk["choices"][0]["delta"].get("content", "")
            if chunk_content in "GOODBYE" and chunk_content != "":
                await actions_queue.put(
                    "greeting"
                )
                await send_personal_message(
                    websocket,
                    json.dumps(
                        {
                            "type": "output",
                            "message": "greeting",
                            "signal": chunk_content
                        }
                    ),
                    client_id,
                )
                continue
            elif chunk_content in "UNKNOWN" and chunk_content != "":
                await actions_queue.put("head_scratch")
                await send_personal_message(
                    websocket,
                    json.dumps(
                        {
                            "type": "output",
                            "message": "head_scratch",
                            "signal": chunk_content
                        }
                    ),
                    client_id,
                )
                continue
            final_answer += chunk_content
        actions = parse_action_robot_in_mall(final_answer)
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
            try:
                actions = actions["actions"]
                for action in actions:
                    await actions_queue.put(

                        action["type"]

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
            except Exception as e:
                print(e)
                pass

    async def server_processor(
        self,
        message_queue: asyncio.Queue,
        actions_queue: asyncio.Queue,
        client_id: str,
        websocket: WebSocket,
    ):

        # obs, _ = self.env.reset()
        main = 0
        zoom = 0
        try:
            steps = 200
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
                        action = await actions_queue.get()
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
                                steps = 80
                                self.env._receive_customer(step)
                            else:

                                if action == "talking":
                                    steps = 80
                                    self.env._receive_customer(step)
                                elif action == "greeting":
                                    steps = 200
                                    self.env._greeting(step)
                                elif action == "head_scratch":
                                    steps = 130
                                    self.env._head_scratch(step)
                                else:
                                    steps = 80
                                    self.env._receive_customer(step)

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
        try:
            await actions_queue.put("greeting")
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
                    await self.handle_text_command(message_data, websocket, client_id, actions_queue)
                elif message_data.get("type") == "voice":
                    await self.handle_voice_command(message_data, websocket, client_id, actions_queue)
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
