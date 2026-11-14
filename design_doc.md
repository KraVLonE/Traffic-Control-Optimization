# Traffic AI Agent Design Document

## Objective
Control the traffic signal of a single 4-way intersection with a Reinforcement Learning agent (tabular Q-learning) so that vehicles spend as little time waiting as possible, and show that it beats classic controllers.

## Architecture Overview
1.  **Environment** (`backend/traffic_env.py`): a custom Gymnasium environment simulating individual vehicles.
2.  **Agent** (`backend/agent.py`): a state encoder plus a Q-table.
3.  **Baselines** (`backend/baselines.py`): fixed-cycle, longest-queue and vehicle-actuated controllers.
4.  **Server** (`backend/main.py`, `backend/simulation.py`): one simulation per WebSocket client, streamed to the React dashboard.

## Environment

Time advances in ticks; 1 tick = 1 simulated second.

-   **Road**: four approaches (N, S, E, W), each 100 units long with 2 parallel lanes (`lanes_per_approach`). A vehicle picks the lane with the most room when it enters and stays in it.
-   **Vehicles**: a mix of bikes (25%), cars (60%) and trucks (15%).

    | Kind  | Length | Max speed | Acceleration |
    |-------|-------:|----------:|-------------:|
    | Bike  |      3 |       2.2 |         0.30 |
    | Car   |      6 |       2.0 |         0.20 |
    | Truck |     12 |       1.6 |         0.12 |

    Vehicles keep a 2-unit gap when stopped. A slow truck holds up whatever is behind it in its lane, so queue discharge is uneven.
-   **Car-following**: each vehicle accelerates towards its own maximum speed but never faster than the speed from which it can still stop behind the vehicle ahead or at a red/yellow stop line.
-   **Signals**: two phases (NS green, EW green). A switch runs 4 ticks of yellow and 1 tick of all-red. Cars too close to stop comfortably when yellow starts run it. A phase must stay green for at least 10 ticks; after 120 ticks it is forced to switch if cross traffic is present.
-   **Demand**: Bernoulli arrivals per lane per tick. `density` is demand as a fraction of intersection capacity (1.0 is roughly saturation). The NS/EW split and per-lane rates are re-sampled every 450 ticks, so the best timing keeps changing. Vehicles that cannot enter a full road wait in an upstream backlog and still count as waiting.
-   **Decisions**: the controller acts every 5 ticks; a switch occupies one decision step.
-   **Seeding**: all randomness comes from the Gymnasium RNG, so `reset(seed=...)` reproduces an episode exactly.

## Reinforcement Learning Formulation

### 1. Observation and State
The raw observation is `[vehicles per approach x4, vehicles near each stop line x4, phase, green_elapsed]`.

The agent encodes it relative to the current phase, which exploits the symmetry of the intersection (experience on one axis transfers to the other):

-   vehicles on the **green** axis (11 buckets)
-   vehicles on the **red** axis (11 buckets)
-   vehicles within 25 units of the **green** stop lines (0, 1, 2, 3+)
-   vehicles within 25 units of the **red** stop lines (0, 1, 2, 3+)
-   green time so far (7 buckets; the first means "minimum green not reached")

That is 13,552 states. Including the green time makes the problem Markov: the agent can tell when a switch is allowed.

### 2. Action Space
-   **Action 0**: keep the current phase.
-   **Action 1**: switch to the other phase (ignored before the minimum green).

### 3. Reward
`reward = -(mean number of waiting vehicles per tick over the decision step)`, where waiting means slower than 0.5 units/tick or held in the upstream backlog. Summed over an episode this is exactly the total waiting time, so maximizing reward minimizes average wait.

### 4. Q-Learning
`Q(s, a) += alpha * (reward + gamma * max_a' Q(s', a') - Q(s, a))`

-   `gamma = 0.95` per decision (an effective horizon of about 100 ticks).
-   `alpha = max(0.02, 1 / visits(s, a)^0.7)`: fast early learning, then averaging over noisy arrivals.
-   Epsilon-greedy, epsilon decaying linearly from 1.0 to 0.02 over the first 70% of training. The zero-initialized table is optimistic (rewards are never positive), which adds systematic exploration.
-   The time limit is a truncation, not a terminal state, so the update still bootstraps.
-   At serve time, states where an action was never tried fall back to a simple actuated rule.

### 5. Training and Evaluation
-   10,000 episodes of 1800 ticks each, at a density drawn uniformly from 0.15 to 1.1.
-   Every 1000 episodes the greedy policy is scored on fixed evaluation seeds and the best table is saved.
-   `evaluate.py` compares the agent with the baselines on a separate set of seeds; all controllers see identical traffic.

## Possible Next Steps
-   Function approximation (DQN) on the raw observation instead of hand-chosen buckets.
-   Lane changing, turning movements and protected left-turn phases.
-   Multiple intersections with coordination.
-   A SUMO backend behind the same Gymnasium interface.
