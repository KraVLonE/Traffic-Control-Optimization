import numpy as np
from mock_env import MockTrafficEnv
from agent import QLearningAgent
import matplotlib.pyplot as plt

def train():
    env = MockTrafficEnv()
    
    # State space shape: 
    # 4 queues (Low, Med, High) -> size 3 each
    # 1 phase (0-1) -> size 2
    state_space_shape = (3, 3, 3, 3, 2)
    action_space_size = env.action_space.n
    
    agent = QLearningAgent(action_space_size, state_space_shape)
    
    episodes = 1000
    rewards_history = []
    
    print("Starting training...")
    
    for episode in range(episodes):
        state, _ = env.reset()
        total_reward = 0
        done = False
        
        while not done:
            action = agent.choose_action(state)
            next_state, reward, terminated, truncated, _ = env.step(action)
            done = terminated or truncated
            
            agent.learn(state, action, reward, next_state)
            
            state = next_state
            total_reward += reward
            
        agent.decay_epsilon()
        rewards_history.append(total_reward)
        
        if (episode + 1) % 100 == 0:
            print(f"Episode {episode + 1}/{episodes}, Total Reward: {total_reward}, Epsilon: {agent.epsilon:.2f}")
            
    print("Training finished.")
    agent.save("q_table.pkl")
    
    # Simple validation run
    print("\nRunning Validation Episode...")
    state, _ = env.reset()
    done = False
    total_reward = 0
    steps = 0
    while not done:
        # Pure exploitation
        action = np.argmax(agent.q_table[tuple(state)])
        state, reward, terminated, truncated, _ = env.step(action)
        done = terminated or truncated
        total_reward += reward
        steps += 1
        # print(f"Step {steps}: State {state}, Action {action}, Reward {reward}")
        
    print(f"Validation Total Reward: {total_reward}")

if __name__ == "__main__":
    train()
