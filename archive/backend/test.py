from services.LLMService import AsyncOpenAIChatCompletionService
import asyncio
async def main():
    api_key = "YOUR_OPENAI_API_KEY"  # Replace with your actual API key
    service = AsyncOpenAIChatCompletionService()  # Enable history

    async def send_message(message: str):
        print(f"\nUser: {message}")
        print("Assistant:", end="", flush=True)
        try:
            async for chunk in service.chat_completion_stream(message):
                print(chunk["choices"][0]["delta"].get("content",""), end="", flush=True)
            print()
        except Exception as e:
            print(f"An error occurred: {e}")

    await send_message("What is the capital of France?")
    # Relies on history
    await send_message("Now, tell me something interesting about it.")
    await send_message("Thanks!")  # another turn with history


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    asyncio.run(main())