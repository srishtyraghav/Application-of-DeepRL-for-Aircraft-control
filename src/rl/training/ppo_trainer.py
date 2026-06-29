import os
import argparse
import sys

# Ensure project root and simulation directories are in the Python search path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "simulation")))

import gymnasium as gym
from stable_baselines3 import PPO
from stable_baselines3.common.monitor import Monitor

# Import environment and helper utilities
from src.rl.aircraft_env import AircraftEnv
from src.rl.training.utils import TrainingLoggerCallback, ensure_directory_exists

"""
================================================================================
REINFORCEMENT LEARNING CONCEPTS & EXPLANATIONS
================================================================================

1. WHAT IS PPO?
   Proximal Policy Optimization (PPO) is an on-policy reinforcement learning 
   algorithm. It belongs to the class of Policy Gradient methods, which optimize 
   the policy (the neural network controlling the agent) directly.

2. WHY IS PPO USED?
   PPO is the industry standard for general RL tasks because:
   - Stability: It uses a "clipped surrogate objective" that prevents the policy 
     from changing too drastically in a single update step. Drastic changes often 
     cause performance collapses.
   - Efficiency: It strikes a great balance between mathematical simplicity, sample 
     complexity, and training speed.
   - Ease of Tuning: It is less sensitive to hyperparameter choices compared to 
     older algorithms like TRPO or DDPG.

3. HOW ARE OBSERVATIONS PASSED TO THE POLICY NETWORK?
   In our environment, `AircraftEnv` compiles a 12-value normalized observation vector:
   `[Norm X, Norm Y, Norm Alt, Norm Heading, Norm Speed, Rel WP X, Rel WP Y, Norm WP Dist, Rel MS X, Rel MS Y, Norm MS Dist, MS Active]`
   This state vector is fed into the input layer of the policy network (a Multi-Layer 
   Perceptron or MLP). The network passes this input through hidden layers to extract 
   flight features.

4. HOW ARE ACTIONS SELECTED?
   The final layer of the policy network outputs raw values (logits) for our 7 discrete actions.
   - During training, these logits are converted to a probability distribution (via softmax), 
     and the agent samples an action. This encourages exploration.
   - During evaluation, the agent selects the action with the highest probability (argmax) 
     for deterministic, optimal performance.

5. HOW DO REWARDS GUIDE LEARNING?
   After the agent takes an action, the environment calculates a reward.
   - Positive rewards (reaching waypoint, evading missile) act as "positive reinforcement", 
     adjusting policy weights to make those actions more likely in similar states.
   - Negative rewards (crashing, getting hit) act as "negative reinforcement", adjusting 
     weights to reduce the likelihood of those actions.

6. WHY IS SAVING/LOADING MODELS IMPORTANT?
   RL training is computationally expensive and can take thousands of episodes. 
   Saving model weights (.zip files) allows us to pause and resume training later, 
   or load the fully trained brain into separate evaluation or production scripts 
   without needing to retrain.
================================================================================
"""

def create_environment():
    """
    Instantiates and wraps the custom Aircraft Gymnasium environment.
    We wrap it in a stable-baselines3 Monitor wrapper to record episode reward 
    telemetry used for logging and tracking progress.
    """
    raw_env = AircraftEnv()
    # Monitor wrapper tracks episode lengths and cumulative rewards
    monitored_env = Monitor(raw_env)
    return monitored_env

def build_ppo_agent(env, lr=3e-4, n_steps=2048, batch_size=64, n_epochs=10, gamma=0.99, clip_range=0.2, ent_coef=0.01):
    """
    Builds a brand-new PPO agent with user-friendly, tunable hyperparameters.
    
    Hyperparameters Explained:
    - learning_rate (lr): Step size of optimization updates. Too large causes instability; 
      too small makes training extremely slow. (Default: 3e-4)
    - n_steps: Number of steps to collect rollouts in the environment before updating the policy. (Default: 2048)
    - batch_size: Mini-batch size used during gradient updates. (Default: 64)
    - n_epochs: Number of epochs to optimize the surrogate loss during each update. (Default: 10)
    - gamma: Discount factor. Closer to 1.0 prioritizes long-term rewards; closer to 0.0 prioritizes immediate rewards. (Default: 0.99)
    - clip_range: Clipping threshold for surrogate objective updates (prevents large policy deviations). (Default: 0.2)
    - ent_coef: Entropy coefficient. Encourages exploration by penalizing premature policy certainty. (Default: 0.01)
    """
    # MlpPolicy is a simple Multi-Layer Perceptron neural network policy (suitable for vector inputs)
    model = PPO(
        policy="MlpPolicy",
        env=env,
        learning_rate=lr,
        n_steps=n_steps,
        batch_size=batch_size,
        n_epochs=n_epochs,
        gamma=gamma,
        clip_range=clip_range,
        ent_coef=ent_coef,
        verbose=1
    )
    return model

def save_agent(model, save_path):
    """
    Saves the PPO model's parameters to a specified zip file.
    """
    # Ensure parent folder exists
    parent_dir = os.path.dirname(save_path)
    if parent_dir:
        ensure_directory_exists(parent_dir)
        
    model.save(save_path)
    print(f"[Model Saved] Successfully saved PPO policy weights to: {save_path}")

def load_agent(load_path, env):
    """
    Loads a previously saved PPO model and attaches it to the environment.
    """
    if not os.path.exists(load_path if load_path.endswith(".zip") else f"{load_path}.zip"):
        raise FileNotFoundError(f"Model file not found at: {load_path}")
        
    model = PPO.load(load_path, env=env)
    print(f"[Model Loaded] Successfully loaded PPO policy from: {load_path}")
    return model

def main():
    # Set up CLI parser to run custom step training easily from command line
    parser = argparse.ArgumentParser(description="Train a PPO agent for Aircraft Control.")
    parser.add_argument("--steps", type=int, default=50000, help="Total timesteps to train the agent.")
    parser.add_argument("--resume", action="store_true", help="Resume training from an existing model.")
    args = parser.parse_args()

    # Define path constants
    MODEL_DIR = "models"
    MODEL_PATH = os.path.join(MODEL_DIR, "ppo_aircraft")
    TOTAL_TIMESTEPS = args.steps

    # Create the environment
    env = create_environment()

    # Initialize model (either create new or resume from existing)
    if args.resume and (os.path.exists(MODEL_PATH + ".zip") or os.path.exists(MODEL_PATH)):
        print(f"[System] Resuming training from existing model: {MODEL_PATH}")
        model = load_agent(MODEL_PATH, env)
    else:
        print("[System] Initializing a brand-new PPO agent...")
        #Tunable hyperparameters stored in clearly named variables
        learning_rate = 3e-4
        n_steps = 2048
        batch_size = 64
        n_epochs = 10
        gamma = 0.99
        clip_range = 0.2
        entropy_coefficient = 0.01
        
        model = build_ppo_agent(
            env=env,
            lr=learning_rate,
            n_steps=n_steps,
            batch_size=batch_size,
            n_epochs=n_epochs,
            gamma=gamma,
            clip_range=clip_range,
            ent_coef=entropy_coefficient
        )

    # Set up progress logger callback
    logger_callback = TrainingLoggerCallback(total_timesteps=TOTAL_TIMESTEPS)

    print(f"[System] Starting PPO training for {TOTAL_TIMESTEPS} total timesteps...")
    
    # Train the agent
    model.learn(total_timesteps=TOTAL_TIMESTEPS, callback=logger_callback, log_interval=10)
    
    # Save the trained model
    save_agent(model, MODEL_PATH)
    print("[System] Training completed successfully!")

if __name__ == "__main__":
    main()
