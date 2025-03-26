import torch
import math
import numpy as np
import genesis as gs
from genesis.utils.geom import (
    quat_to_xyz,
    xyz_to_quat,
    transform_by_quat,
    inv_quat,
    transform_quat_by_quat,
)


def gs_rand_float(lower, upper, shape, device):
    return (upper - lower) * torch.rand(size=shape, device=device) + lower


class G1Env:
    def __init__(
        self,
        num_envs,
        env_cfg,
        obs_cfg,
        reward_cfg,
        command_cfg,
        domain_rand_cfg,
        show_viewer=False,
        device="cuda",
        scene_config={},
    ):
        self.device = torch.device(device)

        self.num_envs = num_envs
        self.num_obs = obs_cfg["num_obs"]
        self.num_privileged_obs = None
        self.num_actions = env_cfg["num_actions"]
        self.num_commands = command_cfg["num_commands"]

        # there is a 1 step latency on real robot, but I'm doing Sim2Sim
        self.simulate_action_latency = False
        self.dt = 0.02  # Control Frequency is 50Hz on Real Robot
        self.max_episode_length = math.ceil(
            env_cfg["episode_length_s"] / self.dt)

        self.env_cfg = env_cfg
        self.obs_cfg = obs_cfg
        self.reward_cfg = reward_cfg
        self.command_cfg = command_cfg
        self.domain_rand_cfg = domain_rand_cfg

        self.obs_scales = obs_cfg["obs_scales"]
        self.reward_scales = reward_cfg["reward_scales"]

        # create scene
        self.scene = gs.Scene(
            sim_options=gs.options.SimOptions(dt=self.dt, substeps=2),
            viewer_options=gs.options.ViewerOptions(
                # max_FPS=int(0.5 / self.dt),
                camera_pos=(2.0, 0.0, 2.5),
                camera_lookat=(0.0, 0.0, 0.5),
                camera_fov=40,
            ),
            vis_options=gs.options.VisOptions(
                n_rendered_envs=1,
                shadow=True,
                ambient_light=[0.7, 0.7, 0.7],
            ),
            rigid_options=gs.options.RigidOptions(
                dt=self.dt,
                constraint_solver=gs.constraint_solver.Newton,
                enable_collision=True,
                enable_self_collision=True,
                enable_joint_limit=True,
            ),
            show_FPS=False,
            show_viewer=show_viewer,
        )

        # add plain
        self.plane = self.scene.add_entity(
            gs.morphs.URDF(file="urdf/plane/plane.urdf",
                           fixed=True, visualization=False)
        )

        # add robot

        robot_config = scene_config.get("robot", {})

        self.base_init_pos = torch.tensor(
            robot_config.get("base_init_pos", self.env_cfg["base_init_pos"]),
            device=self.device,
        )
        self.base_init_quat = torch.tensor(
            robot_config.get("base_init_quat", self.env_cfg["base_init_quat"]),
            device=self.device,
        )
        self.inv_base_init_quat = inv_quat(self.base_init_quat)
        self.robot = self.scene.add_entity(
            gs.morphs.URDF(
                file="assets/g1/g1_23dof_rev_1_0.urdf",
                pos=self.base_init_pos.cpu().numpy(),
                quat=self.base_init_quat.cpu().numpy(),
                scale=1.3,
                fixed=True,
                convexify=True,
            ),
        )
        self.cam = self.scene.add_camera(
            res=(640, 480),
            pos=(-3, 0, 0.3),
            lookat=(1, 0.0, 0.0),
            fov=40,
            GUI=False,
        )
        self.cam_first = self.scene.add_camera(
            res=(640, 480),
            pos=(0.3, 0, 0.3),
            lookat=(1, 0.0, 0.0),
            fov=40,
            GUI=False,
        )
        self.cam_god = self.scene.add_camera(
            res=(640, 480),
            pos=(-5.0, -5.0, 3),
            lookat=(3, 0.0, 0.5),
            fov=40,
            GUI=False,
        )

        self.build_scene_from_config(scene_config)
        # add mall
        reception_scene = self.scene.add_entity(
            gs.morphs.Mesh(file='assets/reception/mall.glb',
                           fixed=True,
                           euler=[90, 0, 0],
                           pos=[0, 0, 0],
                           collision=False,
                           #    decompose_nonconvex=True, coacd_options=coacd_options,
                           #    decimate=True,
                           #    convexify=True,
                           visualization=True,
                           #    parse_glb_with_trimesh=True,
                           ), vis_mode='visual',
        )
        # add bounding box
        desk_bound_box = self.scene.add_entity(
            gs.morphs.MJCF(file='assets/reception/desk_bounding_box.xml', 
                        visualization=False,
                        ),
            vis_mode='visual',
        )

        # build
        self.scene.build(n_envs=num_envs)

        # names to indices
        self.motor_dofs = [
            self.robot.get_joint(name).dof_idx_local
            for name in self.env_cfg["dof_names"]
        ]

        # PD control parameters
        self.robot.set_dofs_kp([self.env_cfg["kp"]] *
                               self.num_actions, self.motor_dofs)
        self.robot.set_dofs_kv([self.env_cfg["kd"]] *
                               self.num_actions, self.motor_dofs)

        # prepare reward functions and multiply reward scales by dt
        self.reward_functions, self.episode_sums = dict(), dict()
        for name in self.reward_scales.keys():
            self.reward_scales[name] *= self.dt
            self.reward_functions[name] = getattr(self, "_reward_" + name)
            self.episode_sums[name] = torch.zeros(
                (self.num_envs,), device=self.device, dtype=gs.tc_float
            )

        # initialize buffers
        self.base_lin_vel = torch.zeros(
            (self.num_envs, 3), device=self.device, dtype=gs.tc_float
        )
        self.base_ang_vel = torch.zeros(
            (self.num_envs, 3), device=self.device, dtype=gs.tc_float
        )
        self.projected_gravity = torch.zeros(
            (self.num_envs, 3), device=self.device, dtype=gs.tc_float
        )
        self.global_gravity = torch.tensor(
            [0.0, 0.0, -1.0], device=self.device, dtype=gs.tc_float
        ).repeat(self.num_envs, 1)
        self.obs_buf = torch.zeros(
            (self.num_envs, self.num_obs), device=self.device, dtype=gs.tc_float
        )
        self.rew_buf = torch.zeros(
            (self.num_envs,), device=self.device, dtype=gs.tc_float
        )
        self.reset_buf = torch.ones(
            (self.num_envs,), device=self.device, dtype=gs.tc_int
        )
        self.episode_length_buf = torch.zeros(
            (self.num_envs,), device=self.device, dtype=gs.tc_int
        )
        self.commands = torch.zeros(
            (self.num_envs, self.num_commands), device=self.device, dtype=gs.tc_float
        )
        self.commands_scale = torch.tensor(
            [
                self.obs_scales["lin_vel"],
                self.obs_scales["lin_vel"],
                self.obs_scales["ang_vel"],
            ],
            device=self.device,
            dtype=gs.tc_float,
        )
        self.actions = torch.zeros(
            (self.num_envs, self.num_actions), device=self.device, dtype=gs.tc_float
        )
        self.last_actions = torch.zeros_like(self.actions)
        self.dof_pos = torch.zeros_like(self.actions)
        self.dof_vel = torch.zeros_like(self.actions)
        self.last_dof_vel = torch.zeros_like(self.actions)
        self.base_pos = torch.zeros(
            (self.num_envs, 3), device=self.device, dtype=gs.tc_float
        )
        self.base_quat = torch.zeros(
            (self.num_envs, 4), device=self.device, dtype=gs.tc_float
        )
        self.default_dof_pos = torch.tensor(
            [
                self.env_cfg["default_joint_angles"][name]
                for name in self.env_cfg["dof_names"]
            ],
            device=self.device,
            dtype=gs.tc_float,
        )
        self.extras = dict()  # extra information for logging

        # Modified Physics
        self.contact_forces = self.robot.get_links_net_contact_force()
        self.left_foot_link = self.robot.get_link(name="left_ankle_roll_link")
        self.right_foot_link = self.robot.get_link(
            name="right_ankle_roll_link")
        self.left_foot_id_local = self.left_foot_link.idx_local
        self.right_foot_id_local = self.right_foot_link.idx_local
        self.feet_indices = [self.left_foot_id_local, self.right_foot_id_local]
        self.feet_num = len(self.feet_indices)
        self.links_vel = self.robot.get_links_vel()
        self.feet_vel = self.links_vel[:, self.feet_indices, :]
        self.links_pos = self.robot.get_links_pos()
        self.feet_pos = self.links_pos[:, self.feet_indices, :]
        period = 0.8
        offset = 0.5
        self.phase = (self.episode_length_buf * self.dt) % period / period
        self.phase_left = self.phase
        self.phase_right = (self.phase + offset) % 1
        self.leg_phase = torch.cat(
            [self.phase_left.unsqueeze(1), self.phase_right.unsqueeze(1)], dim=-1
        )
        self.sin_phase = torch.sin(2 * np.pi * self.phase).unsqueeze(1)
        self.cos_phase = torch.cos(2 * np.pi * self.phase).unsqueeze(1)
        self.pelvis_link = self.robot.get_link(name="pelvis")
        self.pelvis_mass = self.pelvis_link.get_mass()
        self.pelvis_id_local = self.pelvis_link.idx_local
        self.pelvis_pos = self.links_pos[:, self.pelvis_id_local, :]
        self.original_links_mass = []
        self.counter = 0

        termination_contact_names = self.env_cfg["terminate_after_contacts_on"]
        self.termination_contact_indices = []
        for name in termination_contact_names:
            link = self.robot.get_link(name)
            link_id_local = link.idx_local
            self.termination_contact_indices.append(link_id_local)
        self.position = self.base_init_pos.cpu().numpy()
        self.robot.control_dofs_position(
            np.array([0, 0, -0.3, 0.3, -0.2, 0, 0, 0, -0.3, 0.3, -0.2, 0]),
            self.motor_dofs,
        )

    def _resample_commands(self, envs_idx):
        self.commands[envs_idx, 0] = gs_rand_float(
            *self.command_cfg["lin_vel_x_range"], (len(envs_idx),), self.device
        )
        self.commands[envs_idx, 1] = gs_rand_float(
            *self.command_cfg["lin_vel_y_range"], (len(envs_idx),), self.device
        )
        self.commands[envs_idx, 2] = gs_rand_float(
            *self.command_cfg["ang_vel_range"], (len(envs_idx),), self.device
        )

    def stand(self):
        self.robot.control_dofs_position(np.zeros(12), self.motor_dofs)
        self.scene.step()

    def step(self, actions, x=0, y=0, angle=0):
        self.actions = torch.clip(
            actions, -
            self.env_cfg["clip_actions"], self.env_cfg["clip_actions"]
        )
        exec_actions = (
            self.last_actions if self.simulate_action_latency else self.actions
        )
        target_dof_pos = (
            exec_actions * self.env_cfg["action_scale"] + self.default_dof_pos
        )
        self.robot.control_dofs_position(target_dof_pos, self.motor_dofs)
        self.scene.step()

        # update buffers
        self.episode_length_buf += 1
        self.base_pos[:] = self.robot.get_pos()
        # For unknown reasons, it gets NaN values in self.robot.get_*() sometimes
        if torch.isnan(self.base_pos).any():
            nan_envs = (
                torch.isnan(self.base_pos).any(
                    dim=1).nonzero(as_tuple=False).flatten()
            )
            self.reset_idx(nan_envs)
        self.base_quat[:] = self.robot.get_quat()
        self.base_euler = quat_to_xyz(
            transform_quat_by_quat(
                torch.ones_like(self.base_quat) * self.inv_base_init_quat,
                self.base_quat,
            )
        )

        inv_base_quat = inv_quat(self.base_quat)
        self.base_lin_vel[:] = transform_by_quat(
            self.robot.get_vel(), inv_base_quat)
        self.base_ang_vel[:] = transform_by_quat(
            self.robot.get_ang(), inv_base_quat)
        self.projected_gravity = transform_by_quat(
            self.global_gravity, inv_base_quat)
        self.dof_pos[:] = self.robot.get_dofs_position(self.motor_dofs)
        self.dof_vel[:] = self.robot.get_dofs_velocity(self.motor_dofs)

        base_pose_cpu = self.base_pos[0].cpu().numpy()
        base_euler_cpu = self.base_euler[0, 2].cpu().numpy()
        self.position[:2] = base_pose_cpu[:2]
        self.position[2] = float(base_euler_cpu)

        self.cam.set_pose(
            pos=base_pose_cpu
            - np.array(
                [
                    3 * math.cos(math.radians(base_euler_cpu)),
                    3 * math.sin(math.radians(base_euler_cpu)),
                    -1,
                ]
            ),
            lookat=(
                1000000 * math.cos(math.radians(base_euler_cpu)),
                1000000 * math.sin(math.radians(base_euler_cpu)),
                1,
            ),
        )

        self.cam_first.set_pose(
            pos=base_pose_cpu
            + np.array(
                [
                    0.3 * math.cos(math.radians(base_euler_cpu)),
                    0.3 * math.sin(math.radians(base_euler_cpu)),
                    1,
                ]
            ),
            lookat=(
                1000000 * math.cos(math.radians(base_euler_cpu)),
                1000000 * math.sin(math.radians(base_euler_cpu)),
                1,
            ),
        )

        # resample commands
        envs_idx = (
            (
                self.episode_length_buf
                % int(self.env_cfg["resampling_time_s"] / self.dt)
                == 0
            )
            .nonzero(as_tuple=False)
            .flatten()
        )
        # self._resample_commands(envs_idx)

        # check termination and reset
        self.pelvis_pos = self.links_pos[:, self.pelvis_id_local, :]
        self.reset_buf = self.episode_length_buf > self.max_episode_length
        self.reset_buf |= (
            torch.abs(self.pelvis_pos[:, 2])
            < self.env_cfg["termination_if_pelvis_z_less_than"]
        )

        time_out_idx = (
            (self.episode_length_buf > self.max_episode_length)
            .nonzero(as_tuple=False)
            .flatten()
        )
        self.extras["time_outs"] = torch.zeros_like(
            self.reset_buf, device=self.device, dtype=gs.tc_float
        )
        self.extras["time_outs"][time_out_idx] = 1.0

        # self.reset_idx(self.reset_buf.nonzero(as_tuple=False).flatten())

        # Domain Randomization
        # if (self.domain_rand_cfg['randomize_friction']):
        #     self.randomize_friction()

        # if (self.domain_rand_cfg['randomize_mass']):
        #     self.randomize_mass()

        # if (self.domain_rand_cfg['push_robots']):
        #     self.push_robots()

        # Modified Physics
        self.contact_forces = self.robot.get_links_net_contact_force()
        self.left_foot_link = self.robot.get_link(name="left_ankle_roll_link")
        self.right_foot_link = self.robot.get_link(
            name="right_ankle_roll_link")
        self.left_foot_id_local = self.left_foot_link.idx_local
        self.right_foot_id_local = self.right_foot_link.idx_local
        self.feet_indices = [self.left_foot_id_local, self.right_foot_id_local]
        self.feet_num = len(self.feet_indices)
        self.links_vel = self.robot.get_links_vel()
        self.feet_vel = self.links_vel[:, self.feet_indices, :]
        self.links_pos = self.robot.get_links_pos()
        self.feet_pos = self.links_pos[:, self.feet_indices, :]
        period = 0.8
        offset = 0.5
        self.phase = (self.episode_length_buf * self.dt) % period / period
        self.phase_left = self.phase
        self.phase_right = (self.phase + offset) % 1
        self.leg_phase = torch.cat(
            [self.phase_left.unsqueeze(1), self.phase_right.unsqueeze(1)], dim=-1
        )
        self.sin_phase = torch.sin(2 * np.pi * self.phase).unsqueeze(1)
        self.cos_phase = torch.cos(2 * np.pi * self.phase).unsqueeze(1)

        # compute reward
        self.rew_buf[:] = 0.0
        for name, reward_func in self.reward_functions.items():
            rew = reward_func() * self.reward_scales[name]
            self.rew_buf += rew
            self.episode_sums[name] += rew

        # compute observations
        self.obs_buf = torch.cat(
            [
                self.base_ang_vel * self.obs_scales["ang_vel"],  # 3
                self.projected_gravity,  # 3
                self.commands * self.commands_scale,  # 3
                (self.dof_pos - self.default_dof_pos)
                * self.obs_scales["dof_pos"],  # 12
                self.dof_vel * self.obs_scales["dof_vel"],  # 12
                self.actions,  # 12
                self.sin_phase,  # 1
                self.cos_phase,  # 1
            ],
            axis=-1,
        )
        self.obs_buf = torch.clip(
            self.obs_buf,
            -self.env_cfg["clip_observations"],
            self.env_cfg["clip_observations"],
        )
        self.obs_buf[:, 6] = x
        self.obs_buf[:, 7] = y
        self.obs_buf[:, 8] = angle

        self.last_actions[:] = self.actions[:]
        self.last_dof_vel[:] = self.dof_vel[:]

        self.counter += 1

        return self.obs_buf, None, self.rew_buf, self.reset_buf, self.extras

    def randomize_friction(self):
        if self.counter % int(self.domain_rand_cfg["push_interval_s"] / self.dt) == 0:
            friction_range = self.domain_rand_cfg["friction_range"]
            self.robot.set_friction_ratio(
                friction_ratio=friction_range[0]
                + torch.rand(self.num_envs, self.robot.n_links)
                * (friction_range[1] - friction_range[0]),
                ls_idx_local=np.arange(0, self.robot.n_links),
            )
            self.plane.set_friction_ratio(
                friction_ratio=friction_range[0]
                + torch.rand(self.num_envs, self.plane.n_links)
                * (friction_range[1] - friction_range[0]),
                ls_idx_local=np.arange(0, self.plane.n_links),
            )

    def randomize_mass(self):
        if self.counter % int(self.domain_rand_cfg["push_interval_s"] / self.dt) == 0:
            added_mass_range = self.domain_rand_cfg["added_mass_range"]
            added_mass = float(
                torch.rand(1).item() *
                (added_mass_range[1] - added_mass_range[0])
                + added_mass_range[0]
            )
            new_mass = max(self.pelvis_mass + added_mass, 0.1)
            self.pelvis_link.set_mass(new_mass)

    def push_robots(self):
        env_ids = torch.arange(self.num_envs, device=self.device)
        push_env_ids = env_ids[
            self.episode_length_buf[env_ids]
            % int(self.domain_rand_cfg["push_interval_s"] / self.dt)
            == 0
        ]
        if len(push_env_ids) == 0:
            return  # No environments to push in this step
        max_vel_xy = self.domain_rand_cfg["max_push_vel_xy"]
        max_vel_rp = self.domain_rand_cfg["max_push_vel_rp"]
        new_base_lin_vel = torch.zeros_like(self.base_lin_vel)
        new_base_abg_vel = torch.zeros_like(self.base_ang_vel)
        new_base_lin_vel[push_env_ids] = gs_rand_float(
            -max_vel_xy, max_vel_xy, (len(push_env_ids), 3), device=self.device
        )
        new_base_abg_vel[push_env_ids] = gs_rand_float(
            -max_vel_rp, max_vel_rp, (len(push_env_ids), 3), device=self.device
        )
        d_vel_xy = new_base_lin_vel - self.base_lin_vel[:, :3]
        d_vel_rp = new_base_abg_vel - self.base_ang_vel[:, :3]
        d_pos = d_vel_xy * self.dt
        d_pos[:, [2]] = 0
        current_pos = self.robot.get_pos()
        new_pos = current_pos[push_env_ids] + d_pos[push_env_ids]
        self.robot.set_pos(new_pos, zero_velocity=False, envs_idx=push_env_ids)
        d_euler = d_vel_rp * self.dt
        current_euler = self.base_euler
        new_euler = current_euler[push_env_ids] + d_euler[push_env_ids]
        new_quat = xyz_to_quat(new_euler)
        self.robot.set_quat(new_quat, zero_velocity=False,
                            envs_idx=push_env_ids)

    def get_observations(self):
        return self.obs_buf

    def get_privileged_observations(self):
        return None

    def reset_idx(self, envs_idx):
        if len(envs_idx) == 0:
            return

        # reset dofs
        self.dof_pos[envs_idx] = self.default_dof_pos
        self.dof_vel[envs_idx] = 0.0
        self.robot.set_dofs_position(
            position=self.dof_pos[envs_idx],
            dofs_idx_local=self.motor_dofs,
            zero_velocity=True,
            envs_idx=envs_idx,
        )

        # reset base
        self.base_pos[envs_idx] = self.base_init_pos
        self.base_quat[envs_idx] = self.base_init_quat.reshape(1, -1)
        self.base_euler = quat_to_xyz(
            transform_quat_by_quat(
                torch.ones_like(self.base_quat) * self.inv_base_init_quat,
                self.base_quat,
            )
        )
        self.robot.set_pos(
            self.base_pos[envs_idx], zero_velocity=False, envs_idx=envs_idx
        )
        self.robot.set_quat(
            self.base_quat[envs_idx], zero_velocity=False, envs_idx=envs_idx
        )
        self.base_lin_vel[envs_idx] = 0
        self.base_ang_vel[envs_idx] = 0
        self.robot.zero_all_dofs_velocity(envs_idx)

        # reset buffers
        self.last_actions[envs_idx] = 0.0
        self.last_dof_vel[envs_idx] = 0.0
        self.episode_length_buf[envs_idx] = 0
        self.reset_buf[envs_idx] = True

        # fill extras
        self.extras["episode"] = {}
        for key in self.episode_sums.keys():
            self.extras["episode"]["rew_" + key] = (
                torch.mean(self.episode_sums[key][envs_idx]).item()
                / self.env_cfg["episode_length_s"]
            )
            self.episode_sums[key][envs_idx] = 0.0

        self._resample_commands(envs_idx)

    def reset(self):
        self.reset_buf[:] = True
        self.reset_idx(torch.arange(self.num_envs, device=self.device, dtype=torch.long))
        return self.obs_buf, None

    # ------------ reward functions----------------
    def _reward_tracking_lin_vel(self):
        # Tracking of linear velocity commands (xy axes)
        lin_vel_error = torch.sum(
            torch.square(self.commands[:, :2] - self.base_lin_vel[:, :2]), dim=1
        )
        return torch.exp(-lin_vel_error / self.reward_cfg["tracking_sigma"])

    def _reward_tracking_ang_vel(self):
        # Tracking of angular velocity commands (yaw)
        ang_vel_error = torch.square(
            self.commands[:, 2] - self.base_ang_vel[:, 2])
        return torch.exp(-ang_vel_error / self.reward_cfg["tracking_sigma"])

    def _reward_lin_vel_z(self):
        # Penalize z axis base linear velocity
        return torch.square(self.base_lin_vel[:, 2])

    def _reward_action_rate(self):
        # Penalize changes in actions
        return torch.sum(torch.square(self.last_actions - self.actions), dim=1)

    def _reward_base_height(self):
        # Penalize base height away from target
        return torch.square(self.base_pos[:, 2] - self.reward_cfg["base_height_target"])

    def _reward_alive(self):
        # Function borrowed from https://github.com/unitreerobotics/unitree_rl_gym
        # which is originally under BSD-3 License
        return 1.0

    def _reward_gait_contact(self):
        # Function borrowed from https://github.com/unitreerobotics/unitree_rl_gym
        # which is originally under BSD-3 License
        res = torch.zeros(self.num_envs, dtype=torch.float, device=self.device)
        for i in range(self.feet_num):
            is_stance = self.leg_phase[:, i] < 0.55
            contact = self.contact_forces[:, self.feet_indices[i], 2] > 1
            res += ~(contact ^ is_stance)
        return res

    def _reward_gait_swing(self):
        res = torch.zeros(self.num_envs, dtype=torch.float, device=self.device)
        for i in range(self.feet_num):
            is_swing = self.leg_phase[:, i] >= 0.55
            contact = self.contact_forces[:, self.feet_indices[i], 2] > 1
            res += ~(contact ^ is_swing)
        return res

    def _reward_contact_no_vel(self):
        # Function borrowed from https://github.com/unitreerobotics/unitree_rl_gym,
        # which is originally under BSD-3 License
        contact = torch.norm(
            self.contact_forces[:, self.feet_indices, :3], dim=2) > 1.0
        contact_feet_vel = self.feet_vel * contact.unsqueeze(-1)
        penalize = torch.square(contact_feet_vel[:, :, :3])
        return torch.sum(penalize, dim=(1, 2))

    def _reward_feet_swing_height(self):
        # Function borrowed from https://github.com/unitreerobotics/unitree_rl_gym,
        # which is originally under BSD-3 License
        contact = torch.norm(
            self.contact_forces[:, self.feet_indices, :3], dim=2) > 1.0
        pos_error = (
            torch.square(self.feet_pos[:, :, 2] -
                         self.reward_cfg["feet_height_target"])
            * ~contact
        )
        return torch.sum(pos_error, dim=(1))

    def _reward_orientation(self):
        # Function borrowed from https://github.com/unitreerobotics/unitree_rl_gym,
        # which is originally under BSD-3 License
        return torch.sum(torch.square(self.projected_gravity[:, :2]), dim=1)

    def _reward_hip_pos(self):
        # Function borrowed from https://github.com/unitreerobotics/unitree_rl_gym,
        # which is originally under BSD-3 License
        return torch.sum(torch.square(self.dof_pos[:, [1, 2, 7, 8]]), dim=1)

    def _reward_ang_vel_xy(self):
        # Function borrowed from https://github.com/unitreerobotics/unitree_rl_gym,
        # which is originally under BSD-3 License
        return torch.sum(torch.square(self.base_ang_vel[:, :2]), dim=1)

    def _reward_dof_vel(self):
        # Function borrowed from https://github.com/unitreerobotics/unitree_rl_gym,
        # which is originally under BSD-3 License
        return torch.sum(torch.square(self.dof_vel), dim=1)

    def build_scene_from_config(self, config_dict):
        """
        Build a scene based on configuration dictionary

        Args:
            config_dict (dict): Dictionary containing scene configuration
        """
        # Extract scene configuration
        scene_config = config_dict.get("scene", {})

        # Add entities to the scene
        entities = scene_config.get("entities", [])
        for entity in entities:
            entity_type = entity.get("type", "")

            if entity_type == "URDF":
                # Add other URDF entities
                self.scene.add_entity(
                    gs.morphs.URDF(
                        file=entity.get("file", ""),
                        pos=entity.get("pos", [0, 0, 0]),
                        quat=entity.get("quat", [1, 0, 0, 0]),
                        fixed=entity.get("fixed", False),
                    ), vis_mode=entity.get("vis_mode", "collision"),
                )

            elif entity_type == "Mesh":
                # Add mesh entities
                mesh_entity = self.scene.add_entity(
                    gs.morphs.Mesh(
                        file=entity.get("file", ""),
                        pos=entity.get("pos", [0, 0, 0]),
                        fixed=entity.get("fixed", True),
                        scale=entity.get("scale", 1.0),
                        euler=entity.get("euler", [0, 0, 0]),
                    ),
                    vis_mode=entity.get("vis_mode", "collision"),
                )

                # Store named entities if needed
                if "name" in entity:
                    setattr(self, entity["name"], mesh_entity)

        # Build the scene with the specified number of environments
    def _greeting(self,step):
        step = step % 200
        # right arm joints
        r_arm_jnt_names = [
            'right_shoulder_pitch_joint',
            'right_shoulder_roll_joint',
            'right_shoulder_yaw_joint',
            'right_elbow_joint',
            'right_wrist_roll_joint',
        ]
        r_arm_dofs_idx = [self.robot.get_joint(name).dof_idx_local for name in r_arm_jnt_names]
        # PD control parameters
        arm_kp = 60
        arm_kd = 20
        self.robot.set_dofs_kp([arm_kp] * len(r_arm_jnt_names), r_arm_dofs_idx)
        self.robot.set_dofs_kv([arm_kd] * len(r_arm_jnt_names), r_arm_dofs_idx)

        default_dof_pos = np.array([0, 0, 0, 0.5, 0])
        arm_wave_dafault_dof_pos = np.array([0, -0.9, -1.5, -0.65, 0])
        target_dof_pos = np.array(arm_wave_dafault_dof_pos)
        # waving arm
        if step <150:
        # for i in range(150):
            # print(i)
            w = 0.5 * np.sin(2 * np.pi * step / 50)  # Sine wave with amplitude 0.2 and period 50
            self.robot.control_dofs_position(target_dof_pos + [0, w, 0, w, 0], r_arm_dofs_idx)
            self.scene.step()
        # return arm to default position
        elif step < 200:
        # for i in range(50):
            self.robot.control_dofs_position(default_dof_pos, r_arm_dofs_idx)
            self.scene.step() 