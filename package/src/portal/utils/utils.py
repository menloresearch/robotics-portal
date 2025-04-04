from io import BytesIO
import numpy as np
import json
import asyncio
import base64
from PIL import Image

import re
import aiohttp
from datetime import datetime
from fastapi import WebSocket
from .system_prompt import SYSTEM_PROMPT_WAREHOUSE

import os
from dotenv import load_dotenv

load_dotenv(dotenv_path=".env")


class Config:
    max_concurrent_users = os.environ.get("MAX_CONCURRENT_USERS", 1)
    openai_base_url = os.environ.get(
        "OPENAI_BASE_URL", "https://openrouter.ai/api/v1/chat/completions"
    )
    llm_model = os.environ.get("LLM_MODEL", "anthropic/claude-3.5-haiku-20241022")
    api_key = os.environ.get("API_KEY", "")
    timeout_seconds = float(os.environ.get("TIMEOUT_SECONDS", 300))
    enable_history = bool(os.environ.get("ENABLE_HISTORY", False))
    tts_url = os.environ.get("TTS_URL", "http://localhost:8880/v1/audio/speech")
    tts_voice = os.environ.get("TTS_VOICE", "af_jessica")
    tts_response_format = os.environ.get("TTS_RESPONSE_FORMAT", "wav")
    stt_url = os.environ.get("STT_URL", "http://localhost:3348/v1/audio/transcriptions")
    stt_model = os.environ.get("STT_MODEL", "tiny")


def parse_action_robot_in_mall(string):
    return {"actions": [{"type": "talking"}]}


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
    system_prompt: str = SYSTEM_PROMPT_WAREHOUSE,
    model: str = Config.llm_model,
    api_key: str = Config.api_key,
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


def encode_numpy_array(arr):
    """
    Encode a NumPy uint8 array to a gzipped base64 string.

    Args:
        arr (numpy.ndarray): Input NumPy uint8 array

    Returns:
        str: Gzipped base64 encoded string representation of the array
    """

    # Ensure the array is uint8 type
    if arr.dtype != np.uint8:
        arr = arr.astype(np.uint8)

    img_pil = Image.fromarray(arr)

    buffer = BytesIO()
    img_pil.save(buffer, format="WebP", quality=80, method=0)
    webp_bytes = buffer.getvalue()
    buffer.close()

    return base64.b64encode(webp_bytes).decode("utf-8")


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


def decode_base64_to_audio(base64_string: str) -> bytes:
    """
    Decode a base64 string to audio bytes and optionally save to file.

    Args:
        base64_string (str): Base64 encoded string
        output_path (Optional[Union[str, Path]]): Path to save the decoded audio file

    Returns:
        bytes: Decoded audio bytes

    Raises:
        ValueError: If the base64 string is invalid
        IOError: If there's an error writing the file
    """
    try:
        audio_bytes = base64.b64decode(base64_string)
        return audio_bytes
    except base64.binascii.Error as e:
        raise ValueError(f"Invalid base64 string: {e}")
    except IOError as e:
        raise IOError(f"Error writing audio file: {e}")


def encode_audio_to_base64(byte_data: bytes) -> str:
    try:
        base64_encoded = base64.b64encode(byte_data).decode("utf-8")
        return base64_encoded
    except IOError as e:
        raise IOError(f"Error reading audio file: {e}")

