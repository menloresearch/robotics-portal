import genesis as gs
import numpy as np
import logging


logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)


class BeatTheDeskEnv:
    def __init__(self, objects) -> None:
        self.kp = [4500, 4500, 3500, 3500, 2000, 2000, 2000, 100, 100]
        self.kv = [450, 450, 350, 350, 200, 200, 200, 10, 10]
        self.force_range = [
            [-87, -87, -87, -87, -12, -12, -12, -100, -100],
            [87, 87, 87, 87, 12, 12, 12, 100, 100],
        ]
        self.init_arm_dofs = [0, 0, 0, 0, 0, 0, 0]
        self.init_finger_dofs = [0.1, 0.1]

        self.arm_jnt_names = [
            "joint1",
            "joint2",
            "joint3",
            "joint4",
            "joint5",
            "joint6",
            "joint7",
        ]

        self.finger_jnt_names = [
            "finger_joint1",
            "finger_joint2",
        ]

        self.scene = gs.Scene(
            viewer_options=gs.options.ViewerOptions(
                camera_pos=(3, 0.6, 2.5),
                camera_lookat=(0.0, 0.6, 0.5),
                camera_fov=30,
                max_FPS=60,
            ),
            show_viewer=False,
            show_FPS=False,
        )

        _ = self.scene.add_entity(gs.morphs.Plane())
        _ = self.scene.add_entity(
            gs.morphs.MJCF(
                file="scenes/desk/furniture/simpleTable.xml",
                pos=(0.5, 0.5, 0),
            ),
        )

        self.robot = self.scene.add_entity(
            gs.morphs.MJCF(
                file="xml/franka_emika_panda/panda.xml",
                pos=(0, 0.5, 0.75),
                euler=(0, 0, 0),
            ),
        )

        self.cam = self.scene.add_camera(
            res=(640, 480),
            pos=(4, 0.5, 2.5),
            lookat=(0, 0.25, 1.2),
            fov=30,
            GUI=False,
        )

        self.cam_god = self.scene.add_camera(
            res=(640, 480),
            pos=(0, 4.5, 2.5),
            lookat=(0, 0, 1.2),
            fov=30,
            GUI=False,
        )

        self.spawn_objs(objects)

        self.scene.build()

        self.arm_dofs_idx = [
            self.robot.get_joint(name).dof_idx_local for name in self.arm_jnt_names
        ]

        self.finger_dofs_idx = [
            self.robot.get_joint(name).dof_idx_local for name in self.finger_jnt_names
        ]

        self.robot.set_dofs_kp(
            kp=np.array(self.kp),
            dofs_idx_local=self.arm_dofs_idx + self.finger_dofs_idx,
        )

        self.robot.set_dofs_kv(
            kv=np.array(self.kv),
            dofs_idx_local=self.arm_dofs_idx + self.finger_dofs_idx,
        )

        self.end_effector = self.robot.get_link("hand")

        self.robot.set_dofs_force_range(
            lower=np.array(self.force_range[0]),
            upper=np.array(self.force_range[1]),
            dofs_idx_local=self.arm_dofs_idx + self.finger_dofs_idx,
        )

        self.robot.set_dofs_position(
            np.array(self.init_arm_dofs),
            self.arm_dofs_idx,
        )

        self.robot.set_dofs_position(
            np.array(self.init_finger_dofs),
            self.finger_dofs_idx,
        )

    def step(self):
        self.scene.step()

    def ik(self, init_qpos, pos):
        self.end_effector = self.robot.get_link("hand")

        qpos = self.robot.inverse_kinematics(
            link=self.end_effector,
            pos=np.array(pos),
            quat=np.array([0, 1, 0, 0]),
            init_qpos=init_qpos,
        )

        return qpos

    def path_to(self, qpos):
        path = self.robot.plan_path(
            # qpos_start=start_pos,
            qpos_goal=qpos,
            num_waypoints=300,  # 2s duration
            timeout=20,
            planner="BITstar",
        )

        return path

    def grasp(self, close):
        if close:
            self.robot.control_dofs_force(
                [-1.5, -1.5],
                self.finger_dofs_idx,
            )
        else:
            self.robot.control_dofs_force(
                [0.2, 0.2],
                self.finger_dofs_idx,
            )

    def spawn_objs(self, arr):
        size = (0.05, 0.05, 0.05)
        for item in arr:
            pos = list(item.values())[0]
            print("cube pos: ", pos)
            self.scene.add_entity(
                gs.morphs.Box(
                    size=size,
                    pos=pos,
                ),
                surface=gs.surfaces.Plastic(
                    color=(1.0, 0.0, 0.0, 1.0),
                    default_roughness=10.0,
                ),
                # vis_mode="visual",
            )
