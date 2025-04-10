import genesis as gs
import numpy as np

from .config import (
    KP,
    KV,
    FORCE_RANGE,
    INIT_ARM_DOFS,
    INIT_FINGER_DOFS,
    ARM_JOINT_NAMES,
    FINGER_JOINT_NAMES,
    COLORS,
    CAMERA_CONFIGS,
    OBJECT_SIZES,
)


class Scene:
    def __init__(self, res) -> None:
        # Config robot
        self._kp = KP
        self._kv = KV
        self._force_range = FORCE_RANGE
        self._arm_jnt_names = ARM_JOINT_NAMES
        self._finger_jnt_names = FINGER_JOINT_NAMES

        self._init_cubes = [
            {"red-cube": [0.4, 0.4, 0]},
            {"black-cube": [0.4, 0.7, 0]},
            {"green-cube": [0.7, 0.4, 0]},
            {"purple-cube": [0.7, 0.7, 0]},
        ]
        self.cubes = []

        self._scene = gs.Scene(
            vis_options=gs.options.VisOptions(
                show_world_frame=False,
            ),
            viewer_options=gs.options.ViewerOptions(
                camera_pos=(3, 0.6, 2.5),
                camera_lookat=(0.0, 0.6, 0.5),
                camera_fov=30,
                max_FPS=30,
            ),
            rigid_options=gs.options.RigidOptions(max_collision_pairs=100),
            show_viewer=False,
            show_FPS=False,
        )

        _ = self._scene.add_entity(
            gs.morphs.Plane(),
        )

        # Add the table platform
        _ = self._scene.add_entity(
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

        self.init_arm_dofs = INIT_ARM_DOFS
        self.init_finger_dofs = INIT_FINGER_DOFS
        self.robot = self._scene.add_entity(
            gs.morphs.MJCF(
                file="xml/franka_emika_panda/panda.xml",
                pos=(0, 0.5, 0),
                euler=(0, 0, 0),
            ),
        )

        self.cam_480 = self._scene.add_camera(
            **CAMERA_CONFIGS["480p"],
            GUI=False,
        )

        self.cam_720 = self._scene.add_camera(
            **CAMERA_CONFIGS["720p"],
            GUI=False,
        )

        self.cam_1080 = self._scene.add_camera(
            **CAMERA_CONFIGS["1080p"],
            GUI=False,
        )

        self.cam_secondary = self._scene.add_camera(
            **CAMERA_CONFIGS["secondary"],
            GUI=False,
        )

        self.spawn_cubes(self._init_cubes)

        self._scene.build()

        if res == 1080:
            self.cam_main = self.cam_1080
        elif res == 720:
            self.cam_main = self.cam_720
        elif res == 480:
            self.cam_main = self.cam_480

        self.arm_dofs_idx = [
            self.robot.get_joint(name).dof_idx_local for name in self._arm_jnt_names
        ]

        self.finger_dofs_idx = [
            self.robot.get_joint(name).dof_idx_local for name in self._finger_jnt_names
        ]

        self.robot.set_dofs_kp(
            kp=np.array(self._kp),
            dofs_idx_local=self.arm_dofs_idx + self.finger_dofs_idx,
        )

        self.robot.set_dofs_kv(
            kv=np.array(self._kv),
            dofs_idx_local=self.arm_dofs_idx + self.finger_dofs_idx,
        )

        self.end_effector = self.robot.get_link("hand")

        self.robot.set_dofs_force_range(
            lower=np.array(self._force_range[0]),
            upper=np.array(self._force_range[1]),
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
        self._scene.step()

    def ik(self, init_qpos, pos):
        self.end_effector = self.robot.get_link("hand")

        qpos = self.robot.inverse_kinematics(
            link=self.end_effector,
            pos=np.array(pos),
            quat=np.array([0, 1, 0, 0]),
            init_qpos=init_qpos,
        )

        return qpos

    def path_to(self, qpos_start, qpos_goal, num_waypoints):
        path = self.robot.plan_path(
            qpos_start=qpos_start,
            qpos_goal=qpos_goal,
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

    def spawn_cubes(self, arr):
        for item in arr:
            for key, value in item.items():
                color, obj = self.parse_color_type(key)
                obj_ = self._scene.add_entity(
                    gs.morphs.Box(
                        size=OBJECT_SIZES,
                        pos=value,
                    ),
                    surface=gs.surfaces.Plastic(
                        color=COLORS[color],
                    ),
                )

                self.cubes.append({key: obj_})

    def get_cubes_locations(self):
        return_list = []
        for obj in self.cubes:
            obj_ = {}
            obj_[list(obj.keys())[0]] = [
                int(float(x) * 100)
                for x in list(list(obj.values())[0].get_pos().cpu().numpy())
            ]
            obj_[list(obj.keys())[0]][2] += 3
            return_list.append(obj_)
        return return_list
