from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import json
import uvicorn
import asyncio
import logging
import torch
import genesis as gs
from go2_env import Go2Env
import os
from contextlib import asynccontextmanager
import pickle
from rsl_rl.runners import OnPolicyRunner
from utils import encode_numpy_array, send_openai_request, parse_json_from_mixed_string
import random

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

policy_walk = None
policy_stand = None
policy_right = None
policy_left = None
env: Go2Env = None


def load_policy():
    global policy_walk, policy_stand, policy_right, policy_left, env
    log_dir = "checkpoints/go2-walking"
    env_cfg, obs_cfg, reward_cfg, command_cfg, train_cfg = pickle.load(
        open("checkpoints/go2-walking/cfgs.pkl", "rb")
    )
    reward_cfg["reward_scales"] = {}

    env = Go2Env(
        num_envs=1,
        env_cfg=env_cfg,
        obs_cfg=obs_cfg,
        reward_cfg=reward_cfg,
        command_cfg=command_cfg,
        show_viewer=False,
    )

    runner = OnPolicyRunner(env, train_cfg, log_dir, device="cpu")
    resume_path = os.path.join(log_dir, "model_500.pt")
    runner.load(resume_path)
    policy_walk = runner.get_inference_policy(device="cuda:0")

    log_dir = f"checkpoints/go2-left"

    env_cfg, obs_cfg, reward_cfg, command_cfg, train_cfg = pickle.load(
        open("checkpoints/go2-left/cfgs.pkl", "rb")
    )
    reward_cfg["reward_scales"] = {}

    runner = OnPolicyRunner(env, train_cfg, log_dir, device="cpu")
    resume_path = os.path.join(log_dir, "model_500.pt")
    runner.load(resume_path)
    policy_left = runner.get_inference_policy(device="cuda:0")

    log_dir = "checkpoints/go2-right"
    env_cfg, obs_cfg, reward_cfg, command_cfg, train_cfg = pickle.load(
        open("checkpoints/go2-right/cfgs.pkl", "rb")
    )
    reward_cfg["reward_scales"] = {}

    runner = OnPolicyRunner(env, train_cfg, log_dir, device="cpu")
    resume_path = os.path.join(log_dir, "model_500.pt")
    runner.load(resume_path)
    policy_right = runner.get_inference_policy(device="cuda:0")

    log_dir = "checkpoints/go2-stand"
    env_cfg, obs_cfg, reward_cfg, command_cfg, train_cfg = pickle.load(
        open("checkpoints/go2-stand/cfgs.pkl", "rb")
    )
    reward_cfg["reward_scales"] = {}

    runner = OnPolicyRunner(env, train_cfg, log_dir, device="cpu")
    resume_path = os.path.join(log_dir, "model_500.pt")
    runner.load(resume_path)
    policy_stand = runner.get_inference_policy(device="cuda:0")
    return


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load the ML mode
    gs.init()
    load_policy()
    yield
    # Clean up the ML models and release the resources


def transform(action, amplitude):
    if action == 0 or action == 1:  # right or left
        amplitude = amplitude * 70/45

    elif action == 3:
        amplitude = amplitude * 120
    return amplitude


def apply_policy(policy, env, obs, num_steps=1000):
    # env.reset()
    for _ in range(num_steps):
        action = policy(obs)
        obs, _, rews, dones, infos = env.step(action)
    return obs


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

    global policy_right, policy_left, policy_stand, policy_walk, env

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
    async def send_personal_message(message: str, target_id: int):
        if target_id in active_connections:
            conn = active_connections[target_id]
            # if conn.client_state != WebSocketState.DISCONNECTED:
            await conn.send_text(message)

    async def broadcast(message: str, exclude_id: int = None):
        for conn_id, conn in list(active_connections.items()):
            # if conn_id != exclude_id and conn.client_state != WebSocketState.DISCONNECTED:
            try:
                await conn.send_text(message)
            except RuntimeError:
                # Connection might have closed during iteration
                pass

    # Notify about new connection
    await send_personal_message(
        json.dumps({"type": "connection_established", "client_id": client_id}),
        client_id,
    )

    # obs, _ = env.reset()
    # Create task for server-side processing

    async def server_processor(message_queue, actions_queue):
        list_actions = [policy_right, policy_left, policy_stand, policy_walk]
        actions_map = {"move_forward": 3,
                       "rotate_left": 1, "rotate_right": 0, "wait": 2}

        obs, _ = env.reset()
        try:

            steps = random.randint(100, 200)
            action = random.randint(0, 3)
            step = 0
            stop = True
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
                    if message.get("type") == "zoom_in":
                        # Simulate some processing delay
                        processed_message = {
                            "type": "response",
                            "content": f"Processed: {message.get('content', '')}",
                            "processed_at": asyncio.get_event_loop().time(),
                            "original": message,
                        }

                        # Send processed result back to client

                    elif message.get("type") == "stop":
                        stop = True
                        # erase the actions queue
                        while not actions_queue.empty():
                            actions_queue.get_nowait()
                            actions_queue.task_done()

                    if (not actions_queue.empty()) and stop == True:
                        action, amptitude = await actions_queue.get()
                        logger.info("action: "+str(action) +
                                    ", am:" + str(amptitude))
                        action = actions_map[action]
                        steps = transform(action, amptitude)
                        logger.info("action: "+str(action) +
                                    ", steps:" + str(steps))
                        step = 0
                        stop = False

                    # render image then send message to client

                    if step < steps:
                        step += 1

                        third_view, _, _, _ = env.cam.render()
                        first_view, _, _, _ = env.cam_first.render()
                        god_view, _, _, _ = env.cam_god.render()
                        with torch.no_grad():
                            if stop:
                                actions = list_actions[2](obs)  # stand
                                obs, _, rews, dones, infos = env.step(actions)
                            else:
                                actions = list_actions[action](obs)
                                obs, _, rews, dones, infos = env.step(actions)
                        # logger.info(third_view.dtype)
                        processed_message = {
                            "type": "streaming_view",
                            "third_view": encode_numpy_array(third_view),
                            "third_view_shape": list(third_view.shape),
                            "first_view": encode_numpy_array(first_view),
                            "first_view_shape": list(first_view.shape),
                            "god_view": encode_numpy_array(god_view),
                            "god_view_shape": list(god_view.shape)
                        }

                        await send_personal_message(
                            json.dumps(processed_message),
                            client_id
                        )
                        print("robot position:", env.position)
                        await asyncio.sleep(0.001)


                    else:
                        step = 0
                        stop = True
                except WebSocketDisconnect:
                    logger.error("Websocket disconnected")
                    raise
                except Exception as e:
                    logger.error(f"Error while rendering: {str(e)}")
                # Mark task as done
                # message_queue.task_done()
        except asyncio.CancelledError:
            logger.info(f"Server processor for client {client_id} cancelled")
        except Exception as e:
            logger.error(f"Server processor error for client {client_id}: {str(e)}")

    # Create task for handling client messages
    async def client_handler(message_queue, actions_queue):
        global env
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
                    robot_position = str(env.position)
                    content += ". Robot is at the position " + robot_position
                    async for chunk in send_openai_request(prompt=content):
                        await send_personal_message(
                            json.dumps(chunk),
                            client_id
                        )
                        final_answer += chunk["choices"][0]["delta"].get("content","")
                    actions = parse_json_from_mixed_string(final_answer)
                    print(final_answer)
                    if actions is None:
                        await send_personal_message(
                            json.dumps(
                                {"type": "error", "message": "can not parse action from LLM"}),
                            client_id
                        )
                    else:
                        actions = actions["actions"]
                        for action in actions:
                            await actions_queue.put((action["type"], action.get("angle", action.get("distance", 0))))

                else:
                    await message_queue.put(message_data)
                print("robot position:", env.position)

                # Acknowledge receipt immediately (optional)
                # await send_personal_message(
                #     json.dumps({"type": "ack", "message_received": True}),
                #     client_id
                # )
        except WebSocketDisconnect:
            logger.info(f"Client {client_id} disconnected")
            raise
        except asyncio.CancelledError:
            logger.info(f"Client handler for client {client_id} cancelled")
        except Exception as e:
            logger.error(f"Client handler error for client {client_id}: {str(e)}")
            raise

    # Run both coroutines concurrently
    server_task = asyncio.create_task(
        server_processor(message_queue, actions_queue))
    client_task = asyncio.create_task(
        client_handler(message_queue, actions_queue))

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
