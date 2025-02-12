from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import random
import genesis as gs
import numpy as np
from typing import List
import asyncio
import uvicorn

app = FastAPI()

# Pydantic model for the gesture request
class GestureRequest(BaseModel):
    gesture: str

# Global variables to store robot state
g1 = None
l_arm_dofs_idx = None
scene = None

# Add these at the top with other globals
current_gesture = None
current_gesture_position = 0.0
target_gesture_position = 0.0

# Predefined movement patterns
def wave_pattern():
    """Generate a simple waving pattern for the robot arm"""
    global current_gesture_position, target_gesture_position
    current_gesture_position = 0.0
    target_gesture_position = 2.0  # Maximum position to move to
    return "w"  # Return which key we're simulating

def random_movement() -> List[np.ndarray]:
    """Generate random movement within safe bounds"""
    # Define joint limits
    joint_limits = [
        (-3.0892, 2.6704),   # shoulder pitch
        (-1.5882, 2.2515),   # shoulder roll
        (-2.618, 2.618),     # shoulder yaw
        (-1.0472, 2.0944),   # elbow
        (-1.97222, 1.97222), # wrist roll
        (-1.61443, 1.61443), # wrist pitch
        (-1.61443, 1.61443), # wrist yaw
    ]
    
    positions = []
    for _ in range(5):  # Generate 5 random positions
        random_pos = np.array([
            random.uniform(min_val, max_val) 
            for min_val, max_val in joint_limits
        ])
        positions.append(random_pos)
    
    # Add return to neutral position
    positions.append(np.zeros(7))
    return positions

@app.post("/gesture")
async def handle_gesture(request: GestureRequest):
    if g1 is None:
        raise HTTPException(status_code=500, detail="Robot not initialized")
    
    global current_gesture
    
    # Map gestures to movement patterns
    movement_patterns = {
        "wave": wave_pattern,
        "pinch": random_movement,
    }
    
    pattern_func = movement_patterns.get(request.gesture)
    if not pattern_func:
        raise HTTPException(status_code=400, detail=f"Unknown gesture: {request.gesture}")
    
    # Start the gesture
    current_gesture = pattern_func()
    
    return {"status": "success", "message": f"Started {request.gesture} gesture"}

def update_gesture():
    """Called in the simulation loop to update gesture movements"""
    global current_gesture, current_gesture_position
    
    if current_gesture == "w":
        movement_speed = 0.1
        if current_gesture_position < target_gesture_position:
            current_gesture_position += movement_speed
            new_pos = np.array([0.0] * 7)
            new_pos[1] = current_gesture_position
            g1.control_dofs_position(new_pos, l_arm_dofs_idx)
        else:
            current_gesture = None  # Gesture complete

def init_robot(scene_ref, g1_ref, dofs_idx):
    """Initialize global robot references"""
    global scene, g1, l_arm_dofs_idx
    scene = scene_ref
    g1 = g1_ref
    l_arm_dofs_idx = dofs_idx

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 