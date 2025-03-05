import asyncio
import websockets
import json
import numpy as np
import base64
import cv2

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

async def connect_websocket():
    try:
        # WebSocket server URL
        uri = "ws://localhost:8000/ws"
        
        # Establish WebSocket connection
        async with websockets.connect(uri, max_size=None) as websocket:
            print(f"Connected to WebSocket server: {uri}")
            
            # Optional: Send an initial message
            await websocket.send("Hello, WebSocket server!")
            
            # Continuously receive and display messages
            while True:
                try:
                    # Wait for and receive a message
                    message = await websocket.recv()
                    
                    # Parse the JSON message
                    processed_message = json.loads(message)
                    
                    # Decode each view
                    third_view = decode_numpy_array(
                        processed_message['third_view'], 
                        tuple(processed_message['third_view_shape'])
                    )
                    
                    # first_view = decode_numpy_array(
                    #     processed_message['first_view'], 
                    #     tuple(processed_message['first_view_shape'])
                    # )
                    
                    # god_view = decode_numpy_array(
                    #     processed_message['god_view'], 
                    #     tuple(processed_message['god_view_shape'])
                    # )
                    
                    # Display images using OpenCV
                    cv2.imshow('Third View', third_view)
                    # cv2.imshow('First View', first_view)
                    # cv2.imshow('God View', god_view)
                    
                    # Wait for a key press (1ms) and check for 'q' to quit
                    key = cv2.waitKey(1)
                    if key & 0xFF == ord('q'):
                        break
                
                except websockets.ConnectionClosed:
                    print("WebSocket connection closed.")
                    break
                except json.JSONDecodeError:
                    print("Error decoding JSON message")
                except Exception as e:
                    print(f"Error processing message: {e}")
    
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        # Close all OpenCV windows
        cv2.destroyAllWindows()

# Run the WebSocket connection
async def main():
    await connect_websocket()

# Use asyncio to run the async main function
if __name__ == "__main__":
    asyncio.run(main())