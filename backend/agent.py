import numpy as np
import pickle

class QLearningAgent:
    def __init__(self, action_space_size, state_space_shape, alpha=0.1, gamma=0.99, epsilon=1.0, epsilon_decay=0.995, min_epsilon=0.01):
        self.action_space_size = action_space_size
        self.alpha = alpha # Learning rate
        self.gamma = gamma # Discount factor
        self.epsilon = epsilon # Exploration rate
        self.epsilon_decay = epsilon_decay
        self.min_epsilon = min_epsilon
        
        # Initialize Q-table
        # State space shape is passed as a tuple, e.g., (21, 21, 21, 21, 2)
        self.q_table = np.zeros(state_space_shape + (action_space_size,))

    def choose_action(self, state):
        # Epsilon-greedy action selection
        if np.random.rand() < self.epsilon:
            return np.random.randint(self.action_space_size)
        else:
            # Exploit: choose action with max Q-value
            # State is a tuple, so we can index directly
            return np.argmax(self.q_table[tuple(state)])

    def learn(self, state, action, reward, next_state):
        # Q-learning update rule
        # Q(s, a) = Q(s, a) + alpha * (reward + gamma * max(Q(s', a')) - Q(s, a))
        
        current_q = self.q_table[tuple(state) + (action,)]
        max_future_q = np.max(self.q_table[tuple(next_state)])
        
        new_q = current_q + self.alpha * (reward + self.gamma * max_future_q - current_q)
        self.q_table[tuple(state) + (action,)] = new_q

    def decay_epsilon(self):
        self.epsilon = max(self.min_epsilon, self.epsilon * self.epsilon_decay)

    def save(self, filename):
        with open(filename, 'wb') as f:
            pickle.dump(self.q_table, f)

    def load(self, filename):
        with open(filename, 'rb') as f:
            self.q_table = pickle.load(f)
