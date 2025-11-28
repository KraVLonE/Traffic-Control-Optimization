# Traffic AI Agent Design Document

## Objective
Develop a Reinforcement Learning agent using Q-learning to control traffic signals and optimize traffic flow (minimize congestion and wait times).

## Architecture Overview
The system consists of:
1.  **Environment**: A simulation of a traffic intersection (using SUMO or a custom Python-based simulation compatible with Gymnasium interface).
2.  **Agent**: A Q-learning agent that observes the state of the intersection and takes actions (change lights).

## Reinforcement Learning Formulation

### 1. State Space (Observation)
The agent needs to know the current traffic situation.
We will define the state as a tuple:
- **Queue Lengths**: Discretized number of cars waiting in each incoming lane (e.g., Low, Medium, High).
- **Current Phase**: The active traffic light phase (e.g., North-South Green, East-West Green).

*Example State*: `(NS_Queue: High, EW_Queue: Low, Phase: NS_Green)`

### 2. Action Space
The agent controls the traffic lights.
- **Action 0**: Keep current phase.
- **Action 1**: Switch to the next phase (with yellow transition).

*Alternatively*: Select the specific phase to activate (e.g., 0: NS_Green, 1: EW_Green).
*Decision*: We will use **Select Phase** for direct control.

### 3. Reward Function
The goal is to reduce waiting time.
- **Reward**: `-(Total Cumulative Wait Time)`
- The agent receives a negative reward equal to the sum of waiting times of all cars. Maximizing this reward is equivalent to minimizing wait time.

### 4. Q-Learning Algorithm
We will use Tabular Q-Learning.
- **Q-Table**: A table mapping `(State, Action)` pairs to Q-values.
- **Update Rule**:
  `Q(s, a) = Q(s, a) + alpha * (reward + gamma * max(Q(s', a')) - Q(s, a))`
  - `alpha`: Learning rate.
  - `gamma`: Discount factor.
  - `epsilon`: Exploration rate (epsilon-greedy strategy).

## Tools & Libraries
- **Python**: Core language.
- **Gymnasium**: For defining the environment interface.
- **NumPy**: For numerical operations and Q-table management.
- **SUMO (Simulation of Urban MObility)**: (Optional for Phase 1, but recommended for realistic traffic). *For the initial backend agent, we might start with a simple custom mock environment to verify the Q-learning logic before connecting to SUMO.*

## Phase 1: Backend Agent
1.  **Mock Environment**: A simple class simulating traffic queues and light changes.
2.  **Agent Class**: Implements `choose_action` and `learn` methods.
3.  **Training Loop**: Runs episodes and updates the Q-table.
