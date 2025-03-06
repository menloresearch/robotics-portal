import numpy as np
import base64
import json
import aiohttp
SYSTEM_PROMPT = """
# Robot Navigation System Prompt

## Task Overview
You are an AI navigation planner for a robot operating in a 2D planar environment. Your goal is to generate a precise sequence of movement commands to guide the robot from its current position to a target location.

## Environment Constraints
- Coordinate System:
  - Robot position: (x, y, theta)
    - x, y: Cartesian coordinates
    - theta: Orientation angle (-180 to 180 degrees) with respect to the x axis
  - Coordinate system: Fixed Cartesian plane
  - Movement granularity: Discrete unit movements

## Allowed Actions
1. `move_forward(distance)`: Move robot forward in current orientation
2. `rotate_left(angle)`: Rotate robot counterclockwise
3. `rotate_right(angle)`: Rotate robot clockwise
4. `wait()`: Pause robot movement

## Output Requirements
Provide a JSON-formatted action sequence that can be directly parsed for robot movement:

<output>
{
  "actions": [
    {"type": "rotate_left", "angle": 45},
    {"type": "move_forward", "distance": 2},
    {"type": "rotate_right", "angle": 30},
    {"type": "move_forward", "distance": 1}
  ]
}
</output>

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
"""

# API_URL = 

async def send_openai_request(
    api_url: str = "http://localhost:8080/v1/chat/completions", 
    prompt: str = "hello", 
    system_prompt: str = "You are a helpful assistant.", 
    model: str = "/home/thuan/.local/share/cortexcpp/models/huggingface.co/unsloth/DeepSeek-R1-Distill-Llama-8B-GGUF/DeepSeek-R1-Distill-Llama-8B-Q6_K.gguf"
):
    """
    Send an async request to a local OpenAI-like API server.
    
    Args:
        api_url (str): The full URL of the API endpoint
        prompt (str): The user's message/prompt
        system_prompt (str, optional): System instruction for the AI. Defaults to a helpful assistant.
        model (str, optional): The model to use. Defaults to "gpt-3.5-turbo".
    
    Returns:
        dict: The API response
    """
    # Prepare the request payload
    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            },
            {
                "role": "user", 
                "content": prompt
            }
        ],
        "top_p":0.9,
        "temperature": 0.7,  # Optional: adjust creativity
        # "max_tokens": 5000    # Optional: limit response length
    }

    # Create an async HTTP session
    async with aiohttp.ClientSession() as session:
        try:
            # Send POST request to the API
            async with session.post(
                api_url, 
                json=payload,
                headers={'Content-Type': 'application/json'}
            ) as response:
                # Check if the request was successful
                if response.status == 200:
                    # Parse and return the response
                    async for chunk in response.content.iter_any():
                        if chunk:
                            # Decode the chunk (assumes JSON lines format)
                            try:
                                chunk_str = chunk.decode('utf-8').strip()
                                
                                # Handle SSE format (data: prefix)
                                if chunk_str.startswith('data: '):
                                    chunk_str = chunk_str[6:]
                                
                                # Skip empty or "data: [DONE]" messages
                                if chunk_str and chunk_str != '[DONE]':
                                    # Parse JSON and yield the content
                                    chunk_data = json.loads(chunk_str)
                                    yield chunk_data
                            except json.JSONDecodeError:
                                # Some chunks might not be valid JSON
                                # This can happen with SSE formatting
                                if '[DONE]' not in chunk_str:
                                    print(f"Warning: Could not parse chunk as JSON: {chunk_str}")
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
    arr_bytes = arr.tobytes()
    
    # Encode to base64
    base64_encoded = base64.b64encode(arr_bytes)
    
    # Convert to string for easier handling
    return base64_encoded.decode('utf-8')

# Function to decode a base64 string back to a NumPy uint8 array
def decode_numpy_array(base64_str, original_shape):
    """
    Decode a base64 string back to a NumPy uint8 array.
    
    Args:
        base64_str (str): Base64 encoded string
        original_shape (tuple): Original shape of the array
    
    Returns:
        numpy.ndarray: Reconstructed NumPy uint8 array
    """
    # Encode back to bytes if it's a string
    if isinstance(base64_str, str):
        base64_bytes = base64_str.encode('utf-8')
    else:
        base64_bytes = base64_str
    
    # Decode base64
    decoded_bytes = base64.b64decode(base64_bytes)
    
    # Reconstruct the NumPy array
    reconstructed_arr = np.frombuffer(decoded_bytes, dtype=np.uint8)
    
    # Reshape to original dimensions
    return reconstructed_arr.reshape(original_shape)

# Example usage
def main():
    # Create a sample uint8 NumPy array
    original_array = np.array([
        [1, 2, 3],
        [4, 5, 6],
        [7, 8, 9]
    ], dtype=np.uint8)
    
    print("Original Array:")
    print(original_array)
    print("Original Shape:", original_array.shape)
    
    # Encode the array
    encoded_str = encode_numpy_array(original_array)
    print("\nBase64 Encoded String:")
    print(encoded_str)
    
    # Decode the array back
    decoded_array = decode_numpy_array(encoded_str, original_array.shape)
    print("\nDecoded Array:")
    print(decoded_array)
    
    # Verify the reconstruction
    print("\nArrays are identical:", np.array_equal(original_array, decoded_array))

# Run the example
if __name__ == "__main__":
    main()