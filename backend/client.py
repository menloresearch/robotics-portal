import asyncio
import websockets
import json
from utils.utils import encode_audio_to_base64, decode_base64_to_audio
import numpy as np
import cv2
from dotenv import load_dotenv
load_dotenv()
from services.AudioService import AudioService
audio_service = AudioService()
audio_service.stt_url = "http://localhost:3348/v1/audio/transcriptions"
def show_byte_image(message):
    nparr = np.frombuffer(message, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)  # Decode as color image

    if img is not None:
        # print(f"Image size: {img.shape}")  # Print image dimensions

        # Display the image using OpenCV
        cv2.imshow("Received Image", img[:,:,::-1])
        cv2.waitKey(1) 

# Configuration
SERVER_ADDRESS = "ws://localhost:8000/ws"  # Replace with your server's address and port
INIT_MESSAGE = {"type": "env", "env": "g1_mall"}  # Replace with your desired init message

audio_question = encode_audio_to_base64(open("/home/thuan/Downloads/where_is_super_market.wav","rb").read())

async def websocket_client():
    """
    Establishes a WebSocket connection, sends an initialization message,
    and then listens for incoming messages from the server indefinitely.
    """
    try:
        async with websockets.connect(SERVER_ADDRESS,open_timeout=None, ping_timeout=None, close_timeout=None) as websocket:
            print(f"Connected to {SERVER_ADDRESS}")

            # Send initialization message
            await websocket.send(json.dumps(INIT_MESSAGE))
            
            await websocket.send(json.dumps({"type":"voice", "content":audio_question}))
            print(f"Sent initialization message: {INIT_MESSAGE}")

            # Listen for incoming messages in a loop
            while True:
                try:
                    message = await websocket.recv()
                    # print(f"Received message: {message}")

                    # Process the received message here.
                    # For example, you might want to parse it as JSON:
                    try:
                        message = json.loads(message)
                        # Do something with the parsed data (e.g., print specific fields)
                        # print(f"Parsed JSON data: {data}")
                        if message.get("type") == "audio":
                            audio_byte = decode_base64_to_audio(message["content"])
                            text = await audio_service.stt(audio_byte)
                            print("Robot answer: ", text)
                        elif message.get("type") == "streaming_view":
                            image_byte = decode_base64_to_audio(message["god_view"])
                            show_byte_image(image_byte)
                        else:
                            # print(message)
                            pass
                            
                    except json.JSONDecodeError:
                        print(f"Received non-JSON message: {message}")

                except websockets.exceptions as e:
                    print(f"Connection closed: {e}")
                    break  # Exit the loop and reconnect
                except Exception as e:  # Catch other potential errors
                    print(f"Error receiving message: {e}")
                    break # Exit the loop and reconnect

    except websockets.exceptions.ConnectionRefusedError:
        print(f"Connection refused to {SERVER_ADDRESS}. Is the server running?")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        # Optionally, add retry logic here


if __name__ == "__main__":
    asyncio.run(websocket_client())  # Use asyncio.run to start the event loop