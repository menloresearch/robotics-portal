import asyncio
from typing import AsyncGenerator, Optional, List, Dict

from config import Config
from utils.system_prompt import SYSTEM_PROMPT, SYSTEM_PROMPT_WAREHOUSE, SYSTEM_PROMPT_MALL
import aiohttp
import json


class AsyncOpenAIChatCompletionService:
    """
    A service for interacting with the OpenAI chat completion API asynchronously,
    yielding response chunks as they become available.  Supports maintaining
    a chat history across multiple calls.
    """

    def __init__(self, config: dict = {}):
        """
        Initializes the service with an OpenAI API key, optional model, and an option to enable chat history.

        Args:
            api_key: Your OpenAI API key.
            model: The name of the OpenAI model to use (default: "gpt-3.5-turbo").
            organization: Optional.  The organization associated with the API key.
            enable_history: Whether to maintain a chat history. If True, the service will remember previous messages.
        """
        self.config = config
        model_config = self.config.get("models", {}).get("llm", {})
        self.api_key = model_config.get("api_key", Config.api_key)
        self.model = model_config.get("model", Config.llm_model)
        self.api_url = model_config.get("api_url", Config.openai_base_url)
        self.enable_history = model_config.get(
            "enable_history", Config.enable_history)
        # Initialize empty chat history
        self.system_prompt = model_config.get(
            "system_prompt", SYSTEM_PROMPT_MALL)
        self.chat_history: List[Dict[str, str]] = []

    async def chat_completion_stream(self, message_content: str, temperature: float = 0.7, max_tokens: int = 10000) -> AsyncGenerator[str, None]:
        """
        Asynchronously generates chat completions and yields response chunks.

        Args:
            message_content: The content of the user's message.
            temperature:  Sampling temperature, between 0 and 2.
            max_tokens:  The maximum number of tokens to generate.

        Yields:
            str:  Individual text chunks from the chat completion response.
        """

        messages: List[Dict[str, str]] = [
            {"role": "system", "content": self.system_prompt}]

        if self.enable_history:
            messages.extend(self.chat_history)  # Add history if enabled

        # Add the current user message
        messages.append({"role": "user", "content": message_content})
        payload = {
            "model": self.model,
            "messages": messages,
            # "top_p": 0.1,
            # "temperature": 0,  # Optional: adjust creativity
            "stream": True,
            # "max_tokens": 5000    # Optional: limit response length
        }
        full_response_content = ""
        async with aiohttp.ClientSession() as session:
            try:
                # Send POST request to the API
                async with session.post(
                    self.api_url,
                    json=payload,
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {self.api_key}",
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
                                    full_response_content += chunk_data["choices"][0]["delta"].get(
                                        "content", "")
                                except json.JSONDecodeError:
                                    # Some chunks might not be valid JSON
                                    # This can happen with SSE formatting
                                    if "[DONE]" not in chunk_str:
                                        print(
                                            f"Warning: Could not parse chunk as JSON: {chunk_str}"
                                        )
                        if self.enable_history:
                            self.chat_history.append(
                                {"role": "user", "content": message_content})
                            self.chat_history.append(
                                {"role": "assistant", "content": full_response_content})
                    else:
                        # Handle error responses
                        error_text = await response.text()
                        print(f"Error: {response.status} - {error_text}")
                        # return None

            except aiohttp.ClientError as e:
                print(f"Request failed: {e}")
                # return None
