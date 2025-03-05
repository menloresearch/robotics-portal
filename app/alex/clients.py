import asyncio
import websockets

async def connect_websocket():
    try:
        # Replace with the WebSocket server URL you want to connect to
        uri = "ws://localhost:8000/ws"
        
        # Establish WebSocket connection
        async with websockets.connect(uri) as websocket:
            print(f"Connected to WebSocket server: {uri}")
            
            # Optional: Send an initial message
            await websocket.send("Hello, WebSocket server!")
            
            # Continuously receive and print messages
            while True:
                try:
                    # Wait for and receive a message
                    message = await websocket.recv()
                    print(f"Received message: {message}")
                
                except websockets.ConnectionClosed:
                    print("WebSocket connection closed.")
                    break
    
    except Exception as e:
        print(f"An error occurred: {e}")

# Run the WebSocket connection
async def main():
    await connect_websocket()

# Use asyncio to run the async main function
if __name__ == "__main__":
    asyncio.run(main())