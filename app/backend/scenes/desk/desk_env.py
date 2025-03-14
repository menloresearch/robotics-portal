import genesis as gs
import numpy as np
import logging

from app.backend.scenes.scene_abstract import SceneAbstract

logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)


class BeatTheDesk(SceneAbstract):
    def __init__(self) -> None:
        self.kp = [4500, 4500, 3500, 3500, 2000, 2000, 2000, 100, 100]
        self.kv = [450, 450, 350, 350, 200, 200, 200, 10, 10]
        self.force_range = [
            [-87, -87, -87, -87, -12, -12, -12, -100, -100],
            [87, 87, 87, 87, 12, 12, 12, 100, 100],
        ]
        self.init_dofs_pos = [0, 0, 0, 0, 0, 0, 0, 1, 1]

        self.arm_jnt_names = [
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

        self.arm_dofs_idx = None

        gs.init(
            backend=gs.gs_backend.gpu,
            precision="32",
        )

        self.scene = gs.Scene(
            viewer_options=gs.options.ViewerOptions(
                camera_pos=(
                    3,
                    0,
                    2.5,
                ),  # the position of the camera physically in meter
                camera_lookat=(
                    0.0,
                    0.0,
                    0.5,
                ),  # the position that the camera will look at
                camera_fov=30,
                max_FPS=60,
            ),
            show_viewer=False,
        )
        self.end_effector = None

        self.robot = None
        self.cam = None
        self.steps = 0
        self.objs = []
        self.begin = []
        self.end = []

    # convert name into index number for ease of control

    def init_build(self):
        _ = self.scene.add_entity(gs.morphs.Plane())
        _ = self.scene.add_entity(
            gs.morphs.MJCF(
                file="furniture/simpleTable.xml",
                pos=(0.4, 0, 0),
            ),
        )

        self.robot = self.scene.add_entity(
            gs.morphs.MJCF(
                file="xml/franka_emika_panda/panda.xml",
                pos=(0, 0, 0.75),
                euler=(0, 0, 0),
            ),
        )

        self.cam = self.scene.add_camera(
            res=(640, 480),
            fov=30,
            GUI=False,
        )

        self.generate_random_objects()

        self.scene.build()

        self.robot.set_dofs_kp(
            kp=np.array(self.kp),
            dofs_idx_local=self.arm_dofs_idx,
        )

        self.robot.set_dofs_kv(
            kv=np.array(self.kv),
            dofs_idx_local=self.arm_dofs_idx,
        )

        self.arm_dofs_idx = [
            self.robot.get_joint(name).dof_idx_local for name in self.arm_jnt_names
        ]

        self.robot.set_dofs_force_range(
            lower=np.array(self.force_range[0]),
            upper=np.array(self.force_range[1]),
            dofs_idx_local=self.arm_dofs_idx,
        )

        self.robot.set_dofs_position(
            np.array(self.init_dofs_pos),
            self.arm_dofs_idx,
        )

        self.cam.set_pose(
            pos=(4.5, 0, 2.5),
            lookat=(0, 0, 1.2),
        )

    def render_cam(self):
        """Render the camera view with the specified id.

        Args:
            id (int, optional): Camera index to render from. Defaults to 0.

        Returns:
            numpy.ndarray: The rendered image from the camera.
        """
        out = self.cam.render()
        return out[0][:, :, ::-1]

    def step(self):
        self.scene.step()

        if self.steps < 200:
            self.robot.control_dofs_position(self.begin[self.steps])

        if self.steps > 300 and self.steps < 400:
            self.grasp(False)

        if self.steps > 400 and self.steps < 500:
            self.grasp(True)

        if self.steps > 500 and self.steps < 700:
            self.robot.control_dofs_position(
                [0, 0, 0, 0, 0, 0, 0, 0, 0],
                self.arm_dofs_idx,
            )

        # if self.steps >= 200 and self.steps < 400:
        #     self.robot.control_dofs_position(self.end[self.steps - 200])

        self.steps += 1
        return self.steps

    def generate_random_objects(self):
        obj = self.scene.add_entity(
            gs.morphs.Box(
                size=(0.05, 0.05, 0.05),
                pos=(0.6, 0, 0.8),
            )
        )

        self.objs.append(obj)

    def path_to(self, pos):
        self.end_effector = self.robot.get_link("hand")

        qpos = self.robot.inverse_kinematics(
            link=self.end_effector,
            pos=np.array(pos[0:3]),
            quat=np.array([0, 1, 0, 0]),
            init_qpos=self.init_dofs_pos,
        )

        path = self.robot.plan_path(
            qpos_start=self.init_dofs_pos,
            qpos_goal=qpos,
            ignore_collision=True,
            num_waypoints=200,  # 2s duration
        )

        return path

    def grasp(self, close):
        if close:
            self.robot.control_dofs_position(
                [0, 0, 0, 0, 0, 0, 0, 0, 0],
                self.arm_dofs_idx,
            )
        else:
            self.robot.control_dofs_position(
                [0, 0, 0, 0, 0, 0, 0, 1, 1],
                self.arm_dofs_idx,
            )
