from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import json
import datetime
import os

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Log file paths
LOG_FILE = "hand_tracking.log"
DATA_FILE = "hand_tracking_data.json"


# Function to log incoming data
def save_to_log(data):
    timestamp = datetime.datetime.now().isoformat()
    log_entry = {"timestamp": timestamp, "data": data}

    with open(LOG_FILE, "a") as file:
        file.write(json.dumps(log_entry) + "\n")


# Function to save hand data persistently
def save_hand_data(data):
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w") as file:
            json.dump([], file)

    with open(DATA_FILE, "r+") as file:
        existing_data = json.load(file)
        existing_data.append(data)
        file.seek(0)
        json.dump(existing_data, file, indent=4)


@app.get("/ping")
async def health_check():
    """ Returns a simple success message to check if the server is reachable. """
    return {"message": "Server is reachable!"}


@app.post("/handtracking")
async def receive_hand_data(request: Request):
    try:
        data = await request.json()
        save_to_log(data)
        return {"message": "Data received successfully!"}
    except Exception as e:
        return {"error": str(e)}


@app.post("/save_hand_data")
async def save_hand_tracking_data(request: Request):
    try:
        data = await request.json()
        save_hand_data(data)
        return {"message": "Hand tracking data saved successfully!"}
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    import uvicorn
    # Run with HTTPS using self-signed certificates
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        ssl_keyfile="key.pem",
        ssl_certfile="cert.pem"
    )