import genesis as gs
import numpy as np
import logging


logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)


class BeatTheDeskEnv:
    def __init__(self, objects, res) -> None:
        self.kp = [4500, 4500, 3500, 3500, 2000, 2000, 2000, 100, 100]
        self.kv = [450, 450, 350, 350, 200, 200, 200, 10, 10]
        self.force_range = [
            [-87, -87, -87, -87, -12, -12, -12, -100, -100],
            [87, 87, 87, 87, 12, 12, 12, 100, 100],
        ]
        self.init_arm_dofs = [0, 0, 0, 0, 0, 0, 0]
        self.init_finger_dofs = [0.1, 0.1]
        self.cubes = []

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
            vis_options=gs.options.VisOptions(
                show_world_frame=False,
            ),
            viewer_options=gs.options.ViewerOptions(
                camera_pos=(3, 0.6, 2.5),
                camera_lookat=(0.0, 0.6, 0.5),
                camera_fov=30,
                max_FPS=30,
            ),
            show_viewer=False,
            show_FPS=False,
            rigid_options=gs.options.RigidOptions(max_collision_pairs=100),
        )

        _ = self.scene.add_entity(
            gs.morphs.Plane(),
        )

        _ = self.scene.add_entity(
            gs.morphs.Box(
                pos=(0.5, 0.5, 0),
                size=(1, 1, 0.02),
                fixed=True,
                collision=False,
            ),
            surface=gs.surfaces.Plastic(
                color=(0.82, 0.71, 0.55, 1.0),
            ),
        )

        self.robot = self.scene.add_entity(
            gs.morphs.MJCF(
                file="xml/franka_emika_panda/panda.xml",
                pos=(0, 0.5, 0),
                euler=(0, 0, 0),
            ),
        )

        self.cam_480 = self.scene.add_camera(
            res=(854, 480),
            pos=(4, 0.5, 2.5),
            lookat=(0, 0.5, 0),
            fov=30,
            GUI=False,
        )

        self.cam_720 = self.scene.add_camera(
            res=(1280, 720),
            pos=(4, 0.5, 2.5),
            lookat=(0, 0.5, 0),
            fov=30,
            GUI=False,
        )

        self.cam_1080 = self.scene.add_camera(
            res=(1920, 1080),
            pos=(4, 0.5, 2.5),
            lookat=(0, 0.5, 0),
            fov=30,
            GUI=False,
        )

        self.cam_secondary = self.scene.add_camera(
            res=(640, 480),
            pos=(0.5, 0.5, 2.5),
            lookat=(0.5, 0.5, 0),
            fov=30,
            GUI=False,
        )

        self.spawn_objs(objects)

        self.scene.build()

        if res == 1080:
            self.cam_main = self.cam_1080
        elif res == 720:
            self.cam_main = self.cam_720
        elif res == 480:
            self.cam_main = self.cam_480

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

    def path_to(self, start_qpos, qpos, num_waypoints):
        path = self.robot.plan_path(
            qpos_start=start_qpos,
            qpos_goal=qpos,
            num_waypoints=num_waypoints,
            timeout=5,
            planner="RRTConnect",
        )

        return path

    def grasp(self, close):
        if close:
            self.robot.control_dofs_position(
                [0, 0],
                self.finger_dofs_idx,
            )
        else:
            self.robot.control_dofs_position(
                [0.05, 0.05],
                self.finger_dofs_idx,
            )

    def parse_color_type(self, color_type_str):
        if "-" in color_type_str:
            color, obj_type = color_type_str.split("-", 1)
            return color, obj_type
        return None, color_type_str

    def spawn_objs(self, arr):
        size = (0.05, 0.05, 0.05)

        # RGBA color tuples (values from 0 to 1)
        colors = {
            "red": (0.94, 0.5, 0.5, 1.0),
            "black": (0.2, 0.2, 0.2, 1.0),
            "green": (0.6, 0.98, 0.6, 1.0),
            "purple": (0.7, 0.5, 0.9, 1.0),
        }

        for item in arr:
            for key, value in item.items():
                color, obj = self.parse_color_type(key)

                if obj == "container":
                    obj_ = self.scene.add_entity(
                        gs.morphs.Box(
                            size=(0.2, 0.15, 0.02),
                            pos=value,
                        ),
                        surface=gs.surfaces.Gold(
                            color=colors[color],
                            default_roughness=1.0,
                        ),
                    )
                    self.cubes.append({key: obj_})

                else:
                    obj_ = self.scene.add_entity(
                        gs.morphs.Box(
                            size=size,
                            pos=value,
                        ),
                        surface=gs.surfaces.Gold(
                            color=colors[color],
                            smooth=True,
                        ),
                    )
                    self.cubes.append({key: obj_})
