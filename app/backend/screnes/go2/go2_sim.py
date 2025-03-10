import os
import pickle
from screnes.screne_abstract import ScreneAbstract
from screnes.go2.go2_env import Go2Env
from rsl_rl.runners import OnPolicyRunner


class Go2Sim(ScreneAbstract):
    def __init__(self):
        super().__init__()
        self.load_policy()

    def load_policy(self,):
        # global policy_walk, policy_stand, policy_right, policy_left, env
        log_dir = "screnes/go2/checkpoints/go2-walking"
        env_cfg, obs_cfg, reward_cfg, command_cfg, train_cfg = pickle.load(
            open("screnes/go2/checkpoints/go2-walking/cfgs.pkl", "rb")
        )
        reward_cfg["reward_scales"] = {}

        env = Go2Env(
            num_envs=1,
            env_cfg=env_cfg,
            obs_cfg=obs_cfg,
            reward_cfg=reward_cfg,
            command_cfg=command_cfg,
            show_viewer=False,
        )

        runner = OnPolicyRunner(env, train_cfg, log_dir, device="cpu")
        resume_path = os.path.join(log_dir, "model_500.pt")
        runner.load(resume_path)
        self.policy_walk = runner.get_inference_policy(device="cuda:0")

        log_dir = "screnes/go2/checkpoints/go2-left"

        env_cfg, obs_cfg, reward_cfg, command_cfg, train_cfg = pickle.load(
            open("screnes/go2/checkpoints/go2-left/cfgs.pkl", "rb")
        )
        reward_cfg["reward_scales"] = {}

        runner = OnPolicyRunner(env, train_cfg, log_dir, device="cpu")
        resume_path = os.path.join(log_dir, "model_500.pt")
        runner.load(resume_path)
        self.policy_left = runner.get_inference_policy(device="cuda:0")

        log_dir = "screnes/go2/checkpoints/go2-right"
        env_cfg, obs_cfg, reward_cfg, command_cfg, train_cfg = pickle.load(
            open("screnes/go2/checkpoints/go2-right/cfgs.pkl", "rb")
        )
        reward_cfg["reward_scales"] = {}

        runner = OnPolicyRunner(env, train_cfg, log_dir, device="cpu")
        resume_path = os.path.join(log_dir, "model_500.pt")
        runner.load(resume_path)
        self.policy_right = runner.get_inference_policy(device="cuda:0")

        log_dir = "screnes/go2/checkpoints/go2-stand"
        env_cfg, obs_cfg, reward_cfg, command_cfg, train_cfg = pickle.load(
            open("screnes/go2/checkpoints/go2-stand/cfgs.pkl", "rb")
        )
        reward_cfg["reward_scales"] = {}

        runner = OnPolicyRunner(env, train_cfg, log_dir, device="cpu")
        resume_path = os.path.join(log_dir, "model_500.pt")
        runner.load(resume_path)
        self.policy_stand = runner.get_inference_policy(device="cuda:0")
        return

    def transform(self, action, amplitude):
        if action == 0 or action == 1:  # right or left
            amplitude = amplitude * 75 / 45

        elif action == 3:
            amplitude = amplitude * 120
        return amplitude

    def apply_policy(self, policy, env, obs, num_steps=1000):
        # env.reset()
        for _ in range(num_steps):
            action = policy(obs)
            obs, _, rews, dones, infos = env.step(action)
        return obs
