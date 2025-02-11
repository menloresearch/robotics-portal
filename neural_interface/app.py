import os
os.environ['OBJC_DISABLE_INITIALIZE_FORK_SAFETY'] = 'YES'

import numpy as np
import genesis as gs
import time

########################## init ##########################
gs.init(backend=gs.metal,
        logging_level='debug')

########################## create a scene ##########################
scene = gs.Scene(show_viewer=True)
print("Scene created with viewer enabled")

########################## entities ##########################
plane = scene.add_entity(gs.morphs.Plane())

g1 = scene.add_entity(
    gs.morphs.URDF(
        file='/Users/rachpradhan/menlo/RoboPilot/neural_interface/g1_description/g1_23dof_rev_1_0.urdf',
        pos   = (0.0, 0.0, 1.0),
        fixed = True
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

# Optional: set control gains ############
# set positional gains
kp_ = 500
kv_ = 30
g1.set_dofs_kp(
    kp             = np.repeat(kp_, len(R_arm_dofs_idx)),
    dofs_idx_local = R_arm_dofs_idx,
)
# set velocity gains
g1.set_dofs_kv(
    kv             = np.repeat(kv_, len(R_arm_dofs_idx)),
    dofs_idx_local = R_arm_dofs_idx,
)

########################## IK Control ##########################
# get the end-effector link
end_effector = g1.get_link('right_wrist_roll_rubber_hand')

# line_points = np.column_stack((x, y, z))
for i in range(500):
    # generate random target position
    commands = np.random.uniform(-1, 1, size=len(R_arm_dofs_idx))
    g1.control_dofs_position(commands, dofs_idx_local=R_arm_dofs_idx)
    
    scene.step()
    
    # Add a small sleep to make the simulation more visible
    time.sleep(0.01)
    
    # Print every 100 steps to show progress
    if i % 100 == 0:
        print(f"Simulation step: {i}")