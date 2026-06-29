import os
import sys
import time
from stable_baselines3 import PPO

# Add the project root and simulation directories to Python's search path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "src", "simulation")))

from src.rl.aircraft_env import AircraftEnv

# Action name mapping for clearer console debug printouts
ACTION_NAMES = {
    0: "Turn Left",
    1: "Turn Right",
    2: "Accelerate",
    3: "Decelerate",
    4: "Climb",
    5: "Dive",
    6: "Maintain Flight"
}

def create_environment() -> AircraftEnv:
    """
    Creates and returns the custom Aircraft control Gymnasium environment.
    
    Gymnasium is the standard API framework used to define custom RL environments, 
    supplying standard step(), reset(), and render() hooks.
    """
    print("[System] Instantiating AircraftEnv environment...")
    env = AircraftEnv()
    return env

def load_model(model_path: str, env: AircraftEnv) -> PPO:
    """
    Loads the trained PPO model weights from the zip archive.
    
    PPO (Proximal Policy Optimization) is a policy gradient algorithm. Loading 
    the model loads the neural network parameters (policy) which compute action 
    predictions from state observations.
    """
    # Check if the model path exists
    resolved_path = model_path if model_path.endswith(".zip") else f"{model_path}.zip"
    if not os.path.exists(resolved_path):
        print(f"[Error] Trained model not found at path: {resolved_path}")
        print("Please train the PPO model first by running: python src/rl/training/ppo_trainer.py")
        sys.exit(1)
        
    print(f"[System] Loading trained PPO model from: {resolved_path}...")
    model = PPO.load(model_path, env=env)
    print("[System] Model loaded successfully!")
    return model

def run_episode(model: PPO, env: AircraftEnv, episode_num: int) -> bool:
    """
    Runs a single simulation episode of inference using the trained PPO model.
    The agent receives state observations and makes deterministic decisions.
    
    Returns:
        bool: True if training loop should continue, False if we want to stop.
    """
    print(f"\n==========================================")
    print(f" STARTING EVALUATION EPISODE {episode_num}")
    print(f"==========================================\n")
    
    # 1. Reset the environment (starts a new episode, gets initial observation)
    # Following Gymnasium's latest API, reset() returns (observation, info_dict)
    observation, info = env.reset()
    
    done = False
    total_reward = 0.0
    steps_count = 0
    
    # Track metrics for the summary
    target_reached = False
    missile_evaded = False
    missile_hit = False
    
    while not done:
        # 2. Query PPO agent for action prediction
        # deterministic=True disables sampling/exploration, forcing optimal pathing
        action, _states = model.predict(observation, deterministic=True)
        # Ensure action is native python integer type for environment step
        action_idx = int(action.item())
        
        # 3. Advance environment state by 1 physics frame
        # Gymnasium API returns: (next_observation, step_reward, terminated, truncated, info)
        observation, reward, terminated, truncated, info = env.step(action_idx)
        
        total_reward += reward
        steps_count += 1
        
        # 4. Render console telemetry
        env.render()
        
        # 5. Extract debug information from environment
        aircraft = env.aircraft
        waypoint_dist = aircraft.distance_to_waypoint
        missile_dist = aircraft.distance_to_missile
        
        action_name = ACTION_NAMES.get(action_idx, "Unknown Action")
        
        # Print step-level debugging information
        print(f" -> Step: {steps_count:04d} | Action: {action_name:<15} | "
              f"Reward: {reward:+.2f} | Pos: ({aircraft.x:.1f}, {aircraft.y:.1f}) | "
              f"Alt: {aircraft.altitude:.1f}m | Speed: {aircraft.speed:.2f} | "
              f"WP Dist: {waypoint_dist:.1f}px | "
              f"MS Dist: {('N/A' if missile_dist > 9000.0 else f'{missile_dist:.1f}px')}")
        
        # Display the custom metadata info dictionary cleanly
        if info:
            info_str = " | ".join(f"{k}: {v}" for k, v in info.items() if k != "reward_breakdown")
            print(f"    [Info] {info_str}")
            
        # Update metrics from info packet
        if info.get("waypoint_reached", False):
            target_reached = True
        if info.get("missile_evaded", False):
            missile_evaded = True
        if info.get("missile_hit", False):
            missile_hit = True

        # Check termination or truncation flags
        if terminated or truncated:
            done = True
            
        # Add a minor delay for readability in console mode
        time.sleep(0.02)

    # 6. Episode Performance Summary
    success = target_reached or (not missile_hit and steps_count >= 1000)
    outcome_str = "SUCCESS (Waypoint Reached)" if target_reached else (
        "SUCCESS (Time Limit Survived)" if success else "FAILURE (Missile Collided / Crashed)"
    )
    
    print(f"\n------------------------------------------")
    print(f" EPISODE {episode_num} PERFORMANCE SUMMARY")
    print(f"------------------------------------------")
    print(f" Outcome         : {outcome_str}")
    print(f" Total Reward    : {total_reward:+.2f}")
    print(f" Episode Length  : {steps_count} steps")
    print(f" Waypoint Reached: {target_reached}")
    print(f" Missile Evaded  : {missile_evaded}")
    print(f" Missile Hit     : {missile_hit}")
    print(f"------------------------------------------\n")
    
    return True

def main():
    MODEL_PATH = "models/ppo_aircraft"
    
    # Create Gymnasium environment
    env = create_environment()
    
    # Load model parameters
    model = load_model(MODEL_PATH, env)
    
    episode_num = 0
    
    print("\n[System] Beginning testing loop. Press Ctrl+C to stop evaluation.")
    
    try:
        while True:
            episode_num += 1
            # Run episodes continuously
            run_episode(model, env, episode_num)
            
            # Short gap between episodes
            time.sleep(1.0)
            
    except KeyboardInterrupt:
        # Handle KeyboardInterrupt gracefully so terminal cursor and state close cleanly
        print("\n[System] KeyboardInterrupt detected. Cleaning up and exiting evaluation script...")
    finally:
        # Clean up resources
        env.close()
        print("[System] Environment closed. Exit completed.")

if __name__ == "__main__":
    main()
