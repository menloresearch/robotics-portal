import genesis as gs
import numpy as np
from pynput import keyboard
import time
import threading
import uvicorn

gs.init(
    backend=gs.gs_backend.metal,
    precision="32",
)

scene = gs.Scene(
    viewer_options=gs.options.ViewerOptions(
        camera_pos=(5, 0, 3),
        camera_lookat=(0.0, 0, 1.0),
        camera_fov=40,
        max_FPS=30,
    ),
    vis_options=gs.options.VisOptions(
        show_world_frame=True,  # visualize the coordinate frame of `world` at its origin
        world_frame_size=1.0,  # length of the world frame in meter
        show_link_frame=False,  # do not visualize coordinate frames of entity links
        show_cameras=False,  # do not visualize mesh and frustum of the cameras added
        plane_reflection=False,  # turn on plane reflection
        ambient_light=(0.1, 0.1, 0.1),  # ambient light setting
    ),
)

plane = scene.add_entity(gs.morphs.Plane())

g1 = scene.add_entity(
    gs.morphs.MJCF(
        file="unitree_ros/robots/g1_description/g1_dual_arm.xml",
    ),
)

scene.build()

# Name: left_shoulder_pitch_joint
# Idx: 1
# Name: right_shoulder_pitch_joint
# Idx: 2
# Name: left_shoulder_roll_joint
# Idx: 3
# Name: right_shoulder_roll_joint
# Idx: 4
# Name: left_shoulder_yaw_joint
# Idx: 5
# Name: right_shoulder_yaw_joint
# Idx: 6
# Name: left_elbow_joint
# Idx: 7
# Name: right_elbow_joint
# Idx: 8
# Name: left_wrist_roll_joint
# Idx: 9
# Name: right_wrist_roll_joint
# Idx: 10
# Name: left_wrist_pitch_joint
# Idx: 11
# Name: right_wrist_pitch_joint
# Idx: 12
# Name: left_wrist_yaw_joint
# Idx: 13
# Name: right_wrist_yaw_joint
# Idx: 14
# Name: world_joint
# Idx: 15

l_arm_jnt_names = [
    "left_shoulder_pitch_joint",
    "left_shoulder_roll_joint",
    "left_shoulder_yaw_joint",
    "left_elbow_joint",
    "left_wrist_roll_joint",
    "left_wrist_pitch_joint",
    "left_wrist_yaw_joint",
]

l_arm_dofs_idx = [g1.get_joint(name).dof_idx_local for name in l_arm_jnt_names]

g1.set_dofs_kp(
    kp=[500] * len(l_arm_jnt_names),
    dofs_idx_local=l_arm_dofs_idx,
)

g1.set_dofs_kv(
    kv=[30] * len(l_arm_jnt_names),
    dofs_idx_local=l_arm_dofs_idx,
)

g1.set_dofs_force_range(
    upper=np.array([25, 25, 25, 25, 25, 5, 5]),
    lower=np.array([-25, -25, -25, -25, -25, -5, -5]),
    dofs_idx_local=l_arm_dofs_idx,
)


def run_sim(scene):
    g1.set_dofs_position(np.array([0] * len(l_arm_jnt_names)), l_arm_dofs_idx)
    movement_speed = 0.1
    current_positions = np.array([0.0] * len(l_arm_jnt_names))

    pressed_keys = set()

    def on_press(key):
        try:
            # Convert key to character if it's alphanumeric
            k = key.char.lower()
            if k in key_mappings:
                pressed_keys.add(k)
        except AttributeError:
            # Handle special keys
            if key == keyboard.Key.space:
                # Reset position
                nonlocal current_positions
                current_positions = np.array([0.0] * len(l_arm_jnt_names))
                g1.control_dofs_position(current_positions, l_arm_dofs_idx)
            elif key == keyboard.Key.esc:
                # Stop listener
                scene.visualizer.viewer.stop()
                return False

    def on_release(key):
        try:
            k = key.char.lower()
            if k in key_mappings:
                pressed_keys.discard(k)
        except AttributeError:
            pass

    # Key mappings for joint control
    # Using Q/A, W/S, E/D, R/F, T/G, Y/H, U/J for the 7 joints
    key_mappings = {
        "q": (0, movement_speed, [-3.0892, 2.6704]),  # Joint 1 positive
        "a": (0, -movement_speed, [-3.0892, 2.6704]),  # Joint 1 negative
        "w": (1, movement_speed, [-1.5882, 2.2515]),  # Joint 2 positive
        "s": (1, -movement_speed, [-1.5882, 2.2515]),  # Joint 2 negative
        "e": (2, movement_speed, [-2.618, 2.618]),  # Joint 3 positive
        "d": (2, -movement_speed, [-2.618, 2.618]),  # Joint 3 negative
        "r": (3, movement_speed, [-1.0472, 2.0944]),  # Joint 4 positive
        "f": (3, -movement_speed, [-1.0472, 2.0944]),  # Joint 4 negative
        "t": (4, movement_speed, [-1.97222, 1.97222]),  # Joint 5 positive
        "g": (4, -movement_speed, [-1.97222, 1.97222]),  # Joint 5 negative
        "y": (5, movement_speed, [-1.61443, 1.61443]),  # Joint 6 positive
        "h": (5, -movement_speed, [-1.61443, 1.61443]),  # Joint 6 negative
        "u": (6, movement_speed, [-1.61443, 1.61443]),  # Joint 7 positive
        "j": (6, -movement_speed, [-1.61443, 1.61443]),  # Joint 7 negative
    }

    listener = keyboard.Listener(on_press=on_press, on_release=on_release)
    listener.start()

    try:
        while listener.is_alive():
            # Process all currently pressed keys
            for key in pressed_keys:
                joint_idx, delta, bound = key_mappings[key]
                current_positions[joint_idx] += delta
                current_positions[joint_idx] = np.clip(
                    current_positions[joint_idx], bound[0], bound[1]
                )

            g1.control_dofs_position(current_positions, l_arm_dofs_idx)
            scene.step()

            # Prevent system overwhelming
            time.sleep(0.01)

    except KeyboardInterrupt:
        print("\nSimulation terminated by user")


gs.tools.run_in_another_thread(fn=run_sim, args=(scene,))

if scene.visualizer.viewer is not None:
    scene.visualizer.viewer.start()
