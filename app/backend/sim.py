import genesis as gs
import numpy as np
import json

gs.init(
    backend=gs.gs_backend.metal,
    precision="32",
)

scene = gs.Scene(
    viewer_options=gs.options.ViewerOptions(
        camera_pos=(3, 0, 2.5),  # the position of the camera physically in meter
        camera_lookat=(0.0, 0.0, 0.5),  # the position that the camera will look at
        camera_fov=30,
        max_FPS=60,
    ),
    show_viewer=False,
)

plane = scene.add_entity(gs.morphs.Plane())

g1 = scene.add_entity(
    gs.morphs.MJCF(
        file="robotics-models/unitree/g1/torso_only/g1_dual_arm.xml",
    ),
)

cam = scene.add_camera(
    res=(640, 480),
    fov=30,
    GUI=False,
)

scene.build()

root_path = "robotics-models/unitree/g1/torso_only/"
with open(root_path + "desc/g1_dual_arm_xml_config.json", "r") as f:
    model_data = json.load(f)

l_arm_jnt_names = [  # refer to the markdown for a full list of joint name
    "left_shoulder_pitch_joint",
    "left_shoulder_roll_joint",
    "left_shoulder_yaw_joint",
    "left_elbow_joint",
    "left_wrist_roll_joint",
    "left_wrist_pitch_joint",
    "left_wrist_yaw_joint",
]

# convert name into index number for ease of control
l_arm_dofs_idx = [g1.get_joint(name).dof_idx_local for name in l_arm_jnt_names]

g1.set_dofs_kp(  # set the proportional gain which determines the force joint use to correct its position error
    # higher means more rigid
    kp=np.array([500] * len(l_arm_jnt_names)),
    dofs_idx_local=l_arm_dofs_idx,
)

g1.set_dofs_kv(  # set the derivative gain which determines the force joint use to correct its velocity error
    # higher means more damping
    kv=np.array([30] * len(l_arm_jnt_names)),
    dofs_idx_local=l_arm_dofs_idx,
)

g1.set_dofs_force_range(  # refer to the json for more information
    lower=np.array(
        [model_data["joints"][name]["limits"]["force"][0] for name in l_arm_jnt_names]
    ),
    upper=np.array(
        [model_data["joints"][name]["limits"]["force"][1] for name in l_arm_jnt_names]
    ),
    dofs_idx_local=l_arm_dofs_idx,
)


def render_cam(
    id: int = 0,
    steps=0,
    zoom: int = 1,
    pan=[0, 0, 0],
    def_pos=np.array([3.5, 0.0, 2.5]),
):
    """
    Render the camera view with the specified id.

    Args:
        id (int, optional): Camera index to render from. Defaults to 0.

    Returns:
        numpy.ndarray: The rendered image from the camera.
    """
    if steps > 200:
        steps = 0
    scene.step()
    steps += 1

    if steps == 100:
        g1.control_dofs_position(
            np.array([-1.5, 0, 0, 0, 0, 0, 0]),
            l_arm_dofs_idx,
        )
    elif steps == 200:
        g1.control_dofs_position(
            np.array([0, 0, 0, 0, 0, 0, 0]),
            l_arm_dofs_idx,
        )

    if id == 0:
        def_pos += np.array(pan)
        lookat = np.array([0.0, 0.0, 0.5])
        curr_pos = def_pos + zoom * (def_pos - lookat)

        cam.set_pose(
            pos=curr_pos,
            lookat=(0, 0, 0.5),
        )

    elif id == 1:
        cam.set_pose(
            pos=(4, 5, 3),
            lookat=(0, 0, 0.5),
        )

    elif id == 2:
        cam.set_pose(
            pos=(4, 5, 2),
            lookat=(0, 0, 0.5),
        )

    out = cam.render()
    return out[0], steps
