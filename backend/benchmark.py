import numpy as np
from mock_env import MockTrafficEnv

def run_heuristic_benchmark():
    env = MockTrafficEnv()
    episodes = 100
    total_rewards = []
    
    print("Running Heuristic Benchmark (Switch if current lane empty)...")
    
    for _ in range(episodes):
        # We need the internal state for the heuristic, not the observation
        # But in a real scenario we'd infer it. 
        # For benchmarking "perfect" play, we'll peek at the state if needed, 
        # or just use the observation if it's sufficient.
        # The observation is discretized, so it's imperfect.
        # Let's use the internal state to get the "Theoretical Maximum" performance.
        
        state, _ = env.reset()
        # env.state gives us exact queues: [N, S, E, W, Phase]
        
        episode_reward = 0
        done = False
        
        while not done:
            n, s, e, w, phase = env.state
            
            action = 0 # Keep
            
            # Heuristic:
            # If current green lanes are empty, and red lanes have cars, switch.
            # Phase 0: NS Green. Phase 1: EW Green.
            
            if phase == 0: # NS Green
                if (n == 0 and s == 0) and (e > 0 or w > 0):
                    action = 1
            else: # EW Green
                if (e == 0 and w == 0) and (n > 0 or s > 0):
                    action = 1
            
            # Also, if queues are getting too long in Red, maybe switch?
            # But "Switch on Empty" is usually optimal for throughput in simple models.
            
            obs, reward, terminated, truncated, _ = env.step(action)
            done = terminated or truncated
            episode_reward += reward
            
        total_rewards.append(episode_reward)
        
    avg_reward = np.mean(total_rewards)
    print(f"Heuristic Average Reward over {episodes} episodes: {avg_reward}")

if __name__ == "__main__":
    run_heuristic_benchmark()
