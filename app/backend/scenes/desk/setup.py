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

    _ = scene.add_entity(gs.morphs.Plane())
    _ = scene.add_entity(
        gs.morphs.MJCF(
            file="furniture_sim/simpleTable.xml",
        ),
    )

    robot = scene.add_entity(
        gs.morphs.MJCF(
            file="xml/franka_emika_panda/panda.xml",
            pos=(-0.4, 0, 0.75),
        ),
    )

    cam = scene.add_camera(
        res=(640, 480),
        fov=30,
        GUI=False,
    )

    scene.build()

    arm_jnt_names = [  # refer to the markdown for a full list of joint name
        "joint1",
        "joint2",
        "joint3",
        "joint4",
        "joint5",
        "joint6",
        "joint7",
        "finger_joint1",
        "finger_joint2",
    ]

    # convert name into index number for ease of control
    arm_dofs_idx = [robot.get_joint(name).dof_idx_local for name in arm_jnt_names]

    robot.set_dofs_kp(
        kp=np.array([4500, 4500, 3500, 3500, 2000, 2000, 2000, 100, 100]),
        dofs_idx_local=arm_dofs_idx,
    )

    robot.set_dofs_kv(
        kv=np.array([450, 450, 350, 350, 200, 200, 200, 10, 10]),
        dofs_idx_local=arm_dofs_idx,
    )

    robot.set_dofs_force_range(
        lower=np.array([-87, -87, -87, -87, -12, -12, -12, -100, -100]),
        upper=np.array([87, 87, 87, 87, 12, 12, 12, 100, 100]),
        dofs_idx_local=arm_dofs_idx,
    )

    robot.set_dofs_position(
        np.array([0, 0, 0, 0, 0, 0, 0, 0, 0]),
        arm_dofs_idx,
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
    scene.step()
    # steps += 1

    robot.control_dofs_position(
        np.array([0, 0, 0, 0, 0, 0, 0, 0, 0]),
        arm_dofs_idx,
    )

    cam.set_pose(
        pos=(3.5, 0, 2.5),
        lookat=(0, 0, 0.5),
    )

    out = cam.render()
    return out[0][:, :, ::-1], steps
