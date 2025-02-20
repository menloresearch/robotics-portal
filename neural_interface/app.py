import os
os.environ['OBJC_DISABLE_INITIALIZE_FORK_SAFETY'] = 'YES'

import numpy as np
import genesis as gs
import time
import signal
import sys

########################## init ##########################
gs.init(backend=gs.metal,
        logging_level='debug',
        precision="32")

########################## create a scene ##########################
scene = gs.Scene(show_viewer=True)

# Center and position camera for better view
if scene.visualizer and scene.visualizer.viewer:
    scene.visualizer.viewer.camera.position = [3.0, 0.0, 2.0]  # Further back, higher up
    scene.visualizer.viewer.camera.target = [0.0, 0.0, 0.5]    # Looking at robot's center

print("Scene created with viewer enabled")

########################## entities ##########################
plane = scene.add_entity(gs.morphs.Plane())

g1 = scene.add_entity(
    gs.morphs.MJCF(
        file='/Users/rachpradhan/menlo/RoboPilot/neural_interface/g1_description/g1_23dof_rev_1_0.xml',
        ),
)

jnt_names = [
    "right_shoulder_pitch_joint",
    "right_shoulder_roll_joint",
    "right_shoulder_yaw_joint",
    "right_elbow_joint",
    "right_ankle_roll_joint",
    "right_wrist_roll_joint"
]
R_arm_dofs_idx = [g1.get_joint(name).dof_idx_local for name in jnt_names]
print(R_arm_dofs_idx)

########################## build ##########################
scene.build()
print("Scene built successfully")

# Set much stronger control gains
kp_ = 5000  # Increased significantly
kv_ = 150   # Increased significantly
g1.set_dofs_kp(
    kp             = np.repeat(kp_, len(R_arm_dofs_idx)),
    dofs_idx_local = R_arm_dofs_idx,
)
g1.set_dofs_kv(
    kv             = np.repeat(kv_, len(R_arm_dofs_idx)),
    dofs_idx_local = R_arm_dofs_idx,
)

# Enable gravity compensation
# g1.gravity_compensation()

########################## IK Control ##########################
def run_sim(scene):
    try:
        # get the end-effector link
        end_effector = g1.get_link('right_wrist_roll_rubber_hand')

        for i in range(500):
            if not scene.is_running:
                break
                
            # generate random target position
            commands = np.random.uniform(-1, 1, size=len(R_arm_dofs_idx))
            g1.control_dofs_position(commands, dofs_idx_local=R_arm_dofs_idx)
            
            scene.step()
            
            # Print every 100 steps to show progress
            if i % 100 == 0:
                print(f"Simulation step: {i}")
            
            time.sleep(0.01)
    except Exception as e:
        print(f"Simulation error: {e}")
    finally:
        scene.stop()

# Handle graceful shutdown
def signal_handler(sig, frame):
    print("\nClosing simulation gracefully...")
    if scene:
        scene.stop()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

# Run simulation in separate thread
gs.tools.run_in_another_thread(fn=run_sim, args=(scene,))

# Start viewer in main thread
try:
    if scene.visualizer is not None and scene.visualizer.viewer is not None:
        print("Starting viewer...")
        scene.visualizer.viewer.start()
    else:
        print("Warning: Viewer not initialized")
except Exception as e:
    print(f"Viewer error: {e}")
finally:
    scene.stop()