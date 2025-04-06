from portal.server import Server
from scenes.desk.simulation import Simulation
import uvicorn
from fastapi import FastAPI

server = Server()

# Set scene options for selection on the frontend
scenes = server.set_scenes(
    [
        {"id": "arm-stack", "name": "Stack"},
        {"id": "arm-place", "name": "Place"},
    ]
)

# Register simulations to be run
server.register_simulations(
    [
        {"id": "arm-stack", "sim": Simulation},
        {"id": "arm-place", "sim": Simulation},
    ]
)

app = FastAPI(title="Fully Self-Contained WebSocket Server")
app.include_router(server.router)

if __name__ == "__main__":
    uvicorn.run("example:app", host="0.0.0.0", port=8000, reload=False)
