import numpy as np
import base64
import json
import cv2
import asyncio

import re
import aiohttp
from datetime import datetime
from fastapi import WebSocket
from config import Config

SYSTEM_PROMPT = """
# Robot Navigation System Prompt

## Task Overview
You are an AI navigation planner for a robot operating in a 2D planar environment. Your goal is to generate a precise sequence of movement commands to guide the robot from its current position to a target location.

## Environment Constraints
- Coordinate System:
  - Robot position: (x, y, angle)
    - x, y: Cartesian coordinates in meter
    - angle: Orientation angle (-180 to 180 degrees) with respect to the x axis. The unit is in DEGREE.
  - Coordinate system: Fixed Cartesian plane
  - Movement granularity: Discrete unit movements

## Allowed Actions
1. `move_forward(distance)`: Move robot forward in current orientation
2. `rotate_left(angle)`: Rotate robot counterclockwise by some degree of angle
3. `rotate_right(angle)`: Rotate robot clockwise by some degree of angle
4. `wait()`: Pause robot movement

## Output Requirements
Provide a JSON-formatted action sequence that can be directly parsed for robot movement:

```json
{
  "actions": [
    {"type": "rotate_left", "angle": 45},
    {"type": "move_forward", "distance": 2},
    {"type": "rotate_right", "angle": 30},
    {"type": "move_forward", "distance": 1}
  ]
}
```

## Planning Constraints
- Minimize total number of actions
- Ensure precise navigation
- Account for robot's current orientation
- Use smallest angle rotations possible
- Prioritize direct paths

## Input Parameters
- Current Robot Position: (current_x, current_y, current_theta)
- Target Position: (target_x, target_y)

## Planning Process
1. Calculate required rotation to align with target
2. Determine optimal path
3. Break down movement into discrete actions
4. Generate JSON action sequence

## Execution Guidelines
- Be precise in angle and distance calculations
- Ensure actions are executable within environment constraints
- Handle edge cases (impossible movements, obstacle avoidance)

## Object list:
- Dragon:
    - Location: (5.0,5.0) 
    - color: green
- Boat: 
    - Location: (10.0,0.0)
    - corlor: red
## IMPORTANT
- all the Coordinates can be float
- Minimize total number of actions
- move_forward can be done with float distance like 4.5, 5.64, ... base on the real position of object.
- always calculate distance to float number that I can use it directly, the result can be rough to 2 decimas
- always decided to use shortest path
- Oy is in the left of Ox
- If the user didn't ask to move or do any actions, just reply as normal
"""

# API_URL =


def parse_json_from_mixed_string(mixed_string):
    """
    Extracts and parses JSON from a string that may contain other content.

    Args:
        mixed_string (str): A string containing JSON somewhere within it

    Returns:
        The parsed Python object from the first valid JSON found

    Raises:
        ValueError: If no valid JSON is found in the string
    """
    # Look for content between ```json and ``` markers
    json_pattern = r"```json\s*([\s\S]*?)\s*```"
    matches = re.findall(json_pattern, mixed_string)

    if matches:
        # Try to parse the first match
        try:
            return json.loads(matches[0])
        except json.JSONDecodeError as e:
            print(f"Found JSON block but failed to parse: {e}")

    # Alternative approach: try to find anything that looks like JSON objects or arrays
    potential_json_pattern = r"(\{[\s\S]*\}|\[[\s\S]*\])"
    potential_matches = re.findall(potential_json_pattern, mixed_string)

    for potential_match in potential_matches:
        try:
            parsed_data = json.loads(potential_match)
            return parsed_data
        except json.JSONDecodeError:
            continue

    # If we get here, no valid JSON was found
    return None


async def send_openai_request(
    api_url: str = Config.openai_base_url,
    prompt: str = "hello",
    system_prompt: str = SYSTEM_PROMPT,
    model: str = Config.llm_model,
):
    """
    Send an async request to a local OpenAI-like API server.

    Args:
        api_url (str): The full URL of the API endpoint
        prompt (str): The user's message/prompt
        system_prompt (str, optional): System instruction for the AI. Defaults to a helpful assistant.
        model (str, optional): The model to use. Defaults to "gpt-3.5-turbo".

    Returns:
        dict: The API response with full text content
    """
    # Load API key from .env file
    from dotenv import load_dotenv
    import os

    # load_dotenv()
    api_key = os.getenv("API_KEY")

    # Prepare the request payload
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ],
        "top_p": 0.1,
        "temperature": 0,  # Optional: adjust creativity
        "stream": True,
        # "max_tokens": 5000    # Optional: limit response length
    }

    # Create an async HTTP session
    async with aiohttp.ClientSession() as session:
        try:
            # Send POST request to the API
            async with session.post(
                api_url,
                json=payload,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {api_key}",
                    "HTTP-Referer": "https://your-site.com",
                    "X-Title": "Robot Navigation System",
                },
            ) as response:
                # Check if the request was successful
                if response.status == 200:
                    # Parse and return the response
                    full_text_content = ""

                    async for chunk in response.content:
                        if chunk:
                            # Decode the chunk (assumes JSON lines format)
                            try:
                                chunk_str = chunk.decode("utf-8").strip()

                                # Handle SSE format (data: prefix)
                                if chunk_str.startswith("data: "):
                                    chunk_str = chunk_str[6:]

                                # Skip empty or "data: [DONE]" messages
                                if chunk_str and chunk_str != "[DONE]":
                                    # Parse JSON and extract content
                                    chunk_data = json.loads(chunk_str)

                                    yield chunk_data
                            except json.JSONDecodeError:
                                # Some chunks might not be valid JSON
                                # This can happen with SSE formatting
                                if "[DONE]" not in chunk_str:
                                    print(
                                        f"Warning: Could not parse chunk as JSON: {chunk_str}"
                                    )
                else:
                    # Handle error responses
                    error_text = await response.text()
                    print(f"Error: {response.status} - {error_text}")
                    # return None

        except aiohttp.ClientError as e:
            print(f"Request failed: {e}")
            # return None


# Function to encode a NumPy uint8 array to base64
def encode_numpy_array(arr):
    """
    Encode a NumPy uint8 array to a base64 string.

    Args:
        arr (numpy.ndarray): Input NumPy uint8 array

    Returns:
        str: Base64 encoded string representation of the array
    """
    # Ensure the array is uint8 type
    if arr.dtype != np.uint8:
        arr = arr.astype(np.uint8)

    # Convert the array to bytes
    success, encoded_frame = cv2.imencode(".jpeg", arr)

    arr_bytes = encoded_frame.tobytes()

    # Encode to base64
    base64_encoded = base64.b64encode(arr_bytes)

    # Convert to string for easier handling
    return base64_encoded.decode("utf-8")


async def send_personal_message(websocket, message: str, target_id: int):
    await websocket.send_text(message)


async def check_timeout(websocket: WebSocket, last_activity_ref):
    while True:
        await asyncio.sleep(10)  # Check every 10 seconds

        # Calculate idle time
        idle_seconds = (datetime.now() - last_activity_ref).total_seconds()

        # Close connection if idle time exceeds timeout
        if idle_seconds >= Config.timeout_seconds:
            print(f"Closing inactive connection after {idle_seconds} seconds")
            await websocket.close(code=1000, reason="Timeout due to inactivity")
            break
