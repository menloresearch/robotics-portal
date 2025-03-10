import genesis as gs
import numpy as np


def build():
    gs.init(
        backend=gs.gs_backend.gpu,
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

    robot = scene.add_entity(
        gs.morphs.MJCF(
            file="../sim-envs/franka_fr3/test.xml",
        ),
    )

    cam = scene.add_camera(
        res=(640, 480),
        fov=30,
        GUI=False,
    )

    scene.build()

    arm_jnt_names = [  # refer to the markdown for a full list of joint name
        "fr3_joint1",
        "fr3_joint2",
        "fr3_joint3",
        "fr3_joint4",
        "fr3_joint5",
        "fr3_joint6",
        "fr3_joint7",
    ]

    # convert name into index number for ease of control
    arm_dofs_idx = [robot.get_joint(name).dof_idx_local for name in arm_jnt_names]

    robot.set_dofs_kp(
        kp=np.array([4500, 4500, 3500, 3500, 2000, 2000, 2000]),
        dofs_idx_local=arm_dofs_idx,
    )

    robot.set_dofs_kv(
        kv=np.array([4500, 4500, 3500, 3500, 2000, 2000, 2000]),
        dofs_idx_local=arm_dofs_idx,
    )

    robot.set_dofs_force_range(
        lower=np.array([-2.7437, -1.7837, 2.9007, -3.0421, -2.8065, 0.5445, -3.0159]),
        upper=np.array([2.7473, 1.7837, 2.9007, -0.1518, 2.8065, 4.5169, 3.0159]),
        dofs_idx_local=arm_dofs_idx,
    )

    return scene, cam, robot, arm_dofs_idx


def render_cam(
    scene,
    cam,
    robot,
    arm_dofs_idx,
    steps=0,
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
        robot.control_dofs_position(
            np.array([-1.5, 0, 0, 0, 0, 0, 0]),
            arm_dofs_idx,
        )

    if steps == 200:
        robot.control_dofs_position(
            np.array([-1.5, 0, 0, 0, 0, 0, 0]),
            arm_dofs_idx,
        )

    cam.set_pose(
        pos=(3.5, 0, 2.5),
        lookat=(0, 0, 0.5),
    )

    out = cam.render()
    return out[0], steps
