import asyncio
import aiohttp
import json
from fastapi import WebSocket, WebSocketDisconnect
from config import Config
from utils.utils import encode_audio_to_base64
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AudioService:
    """
    A class to manage speech-to-text (STT) and text-to-speech (TTS) services.

    Attributes:
        tts_url (str): The URL for the text-to-speech service.
        stt_url (str): The URL for the speech-to-text service.
        llm_text_queue (asyncio.Queue): An asynchronous queue to receive text from an LLM.
    """

    def __init__(self, config: dict = {}):
        """
        Initializes the AudioService with the TTS and STT URLs and queues.

        Args:
            tts_url (str): The URL for the text-to-speech service.
            stt_url (str): The URL for the speech-to-text service.
        """
        self.config = config
        model_config = self.config.get("models", {}).get("audio", {})
        self.tts_url = model_config.get("tts_url", Config.tts_url)
        self.stt_url = model_config.get("stt_url", Config.stt_url)
        self.llm_text_queue = asyncio.Queue()  # Queue for LLM text to TTS

    async def stt(self, audio_data: bytes) -> str:
        """
        Asynchronously calls the STT service with audio data and returns the transcribed text.

        Args:
            audio_data (bytes): The audio data to send to the STT service.

        Returns:
            str: The transcribed text from the STT service.

        Raises:
            aiohttp.ClientResponseError: If the STT service returns an error status.
            Exception: For other errors during the STT call.
        """
        try:
            async with aiohttp.ClientSession() as session:
                data = aiohttp.FormData()
                data.add_field('file',
                               audio_data,
                               filename=f"file.wav",
                               content_type="audio/wav")
                data.add_field("model", "tiny")
                async with session.post(self.stt_url, data=data) as response:
                    response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
                    response_json = await response.json()
                    # Assuming response has "text" field
                    return response_json.get("text", "")
        except aiohttp.ClientResponseError as e:
            logger.info(f"STT service error: {e}")
            raise
        except Exception as e:
            logger.info(f"Error during STT call: {e}")
            raise

    async def send_to_tts(self, session, text, websocket):
        body = {"input": text, "model": "kokoro", "voice": Config.tts_voice,
                "response_format": Config.tts_response_format, "stream": False}
        async with session.post(self.tts_url, json=body) as response:
            byte = await response.read()
            # logger.info("Putting bytes:" ,len(byte), str(datetime.now()))
            await websocket.send_text(json.dumps(
                {"type": "audio", "content": encode_audio_to_base64(byte)}))

    async def stream_tts(self,  websocket: WebSocket):
        """
        Helper function to stream TTS audio to the websocket in chunks.

        Args:
            text (str): The text to convert to speech.
            websocket (Websocket): The websocket to send audio chunks.

        Raises:
            aiohttp.ClientResponseError: If the TTS service returns an error status.
            websockets.ConnectionClosedError: If the websocket connection is closed during streaming.
            Exception: For other errors during the TTS call.
        """
        final_answer = ""
        answer = ""
        tokens_processed = 0
        chunk_size = 10
        currentCount = 0
        try:
            
            # Assuming your TTS service expects a JSON payload
            while True:
                if not self.llm_text_queue.empty():
                    async with aiohttp.ClientSession() as session:
                        message = await self.llm_text_queue.get()
                        if message is None: # End of turn
                            if answer:
                                await self.send_to_tts(session, answer, websocket)
                                logger.info(answer)
                            break
                        object = message

                        if object["choices"][0]["delta"].get("content"):
                            delta_content = object["choices"][0]["delta"]["content"]
                            final_answer += delta_content

                            if currentCount < chunk_size:
                                answer += delta_content
                            elif currentCount < 60 and delta_content in [".", ",", ":", ";"]:
                                await self.send_to_tts(session, answer, websocket)
                                logger.info(answer)
                                answer = ""  # Reset answer
                                currentCount = 0
                                chunk_size = 60
                            elif chunk_size == 10:
                                answer += delta_content
                            else:
                                await self.send_to_tts(session, answer, websocket)
                                logger.info(answer)
                                answer = delta_content  # Reset answer
                                currentCount = 0
                                if chunk_size == 60:
                                    chunk_size = 200

                            tokens_processed += 1
                            currentCount += 1
                else:
                    await asyncio.sleep(0.01)
        except aiohttp.ClientResponseError as e:
            logger.info(f"TTS service error: {e}")
            raise
        except WebSocketDisconnect:
            logger.info("Websocket connection closed during TTS streaming.")
            raise  # Re-raise so the calling function knows about the closure
        except Exception as e:
            logger.info(f"Error during TTS streaming: {e}")
            raise
