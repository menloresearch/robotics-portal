import asyncio
import aiohttp
import json
# ./llama-server -m ~/.local/share/cortexcpp/models/huggingface.co/unsloth/DeepSeek-R1-Distill-Llama-8B-GGUF/DeepSeek-R1-Distill-Llama-8B-Q6_K.gguf  -c 16000 -cb -ctk q8_0 -ctv q8_0 -fa -ngl 33 --host 0.0.0.0

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

async def send_openai_request(
    api_url: str, 
    prompt: str, 
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
                "content": system_prompt
            },
            {
                "role": "user", 
                "content": prompt
            }
        ],
        "top_p":0.9,
        "temperature": 0.7,  # Optional: adjust creativity
        "max_tokens": 5000 ,   # Optional: limit response length
        # "stream": True
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
                    response_data = await response.json()
                    return response_data
                else:
                    # Handle error responses
                    error_text = await response.text()
                    print(f"Error: {response.status} - {error_text}")
                    return None
        
        except aiohttp.ClientError as e:
            print(f"Request failed: {e}")
            return None

async def main():
    # Local API URL (modify to match your local server)
    api_url = "http://localhost:8080/v1/chat/completions"
    
    # Example prompts
    user_prompt = "Go to dragon. Current robot position is (0,0,0)"
    system_prompt = SYSTEM_PROMPT
    # Send the request
    response = await send_openai_request(
        api_url, 
        prompt=user_prompt, 
        system_prompt=system_prompt
    )
    
    # Process and print the response
    if response:
        # Extract and print the AI's response
        try:
            ai_response = response['choices'][0]['message']['content']
            print("AI Response:")
            print(ai_response)
        except (KeyError, IndexError) as e:
            print("Error parsing response:", e)
            print("Full response:", json.dumps(response, indent=2))

# Run the async main function
if __name__ == "__main__":
    asyncio.run(main())