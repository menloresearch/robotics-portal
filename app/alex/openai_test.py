import asyncio
import aiohttp
import json
# ./llama-server -m ~/.local/share/cortexcpp/models/huggingface.co/unsloth/DeepSeek-R1-Distill-Llama-8B-GGUF/DeepSeek-R1-Distill-Llama-8B-Q6_K.gguf  -c 16000 -cb -ctk q8_0 -ctv q8_0 -fa -ngl 33 --host 0.0.0.0
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
        "temperature": 0.7,  # Optional: adjust creativity
        "max_tokens": 150    # Optional: limit response length
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
    user_prompt = "Explain quantum computing in simple terms."
    system_prompt = "You are a scientific explainer. Break down complex topics into easy-to-understand language. Think carefully before answer and put all thinking section inside the <think></think> tag"
    
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