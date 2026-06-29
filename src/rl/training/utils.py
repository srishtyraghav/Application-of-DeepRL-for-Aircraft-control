import os
import numpy as np
from stable_baselines3.common.callbacks import BaseCallback

class TrainingLoggerCallback(BaseCallback):
    """
    Custom Stable-Baselines3 Callback for clean and structured logging of 
    reinforcement learning training metrics.
    
    Why use a callback?
    In Reinforcement Learning, callbacks allow us to inject custom code at 
    specific steps of the training loop (e.g. after each environment step).
    This lets us track rolling episode rewards, lengths, and print training progress.
    """
    def __init__(self, total_timesteps: int, check_freq: int = 1000, verbose: int = 0):
        super(TrainingLoggerCallback, self).__init__(verbose)
        self.total_timesteps = total_timesteps
        self.check_freq = check_freq
        self.episode_count = 0
        self.episode_rewards = []
        
    def _on_step(self) -> bool:
        """
        This method is called by the trainer after every step in the environment.
        """
        # Look for episode telemetry in environment info
        for info in self.locals.get("infos", []):
            if "episode" in info.keys():
                self.episode_count += 1
                ep_reward = info["episode"]["r"]
                ep_length = info["episode"]["l"]
                self.episode_rewards.append(ep_reward)
                
                # Compute rolling average reward of the last 20 episodes
                rolling_window = 20
                avg_reward = np.mean(self.episode_rewards[-rolling_window:])
                
                # Compute training percentage progress
                progress_percent = (self.num_timesteps / self.total_timesteps) * 100.0
                
                # Print structured, readable logs to the terminal
                print(f"[Training Progress] | Episode: {self.episode_count:04d} | "
                      f"Steps: {self.num_timesteps:06d}/{self.total_timesteps:06d} ({progress_percent:.1f}%) | "
                      f"Reward: {ep_reward:+.2f} | "
                      f"Avg Reward (last {min(len(self.episode_rewards), rolling_window)}): {avg_reward:+.2f} | "
                      f"Length: {ep_length:d}")
                
        return True

def ensure_directory_exists(directory_path: str):
    """
    Checks if a directory exists and creates it if it doesn't.
    """
    if not os.path.exists(directory_path):
        os.makedirs(directory_path)
        print(f"[System] Created directory: {directory_path}")
