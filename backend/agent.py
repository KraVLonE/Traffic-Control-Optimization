"""Tabular Q-learning agent for the traffic signal environment."""
import numpy as np

from traffic_env import KEEP, SWITCH

# Bucket edges used to discretise the raw observation.
COUNT_EDGES = (1, 2, 3, 5, 7, 10, 14, 19, 26, 36)   # vehicles on an axis
ELAPSED_EDGES = (10, 15, 20, 30, 45, 70)           # ticks of green so far
NEAR_CAP = 3                                       # vehicles at a stop line: 0, 1, 2, 3+


class StateEncoder:
    """Maps a raw observation to a small discrete state.

    The intersection is symmetric, so the state is expressed relative to the
    current phase ("green axis" / "red axis") instead of NS / EW. This halves
    the table and lets experience on one axis transfer to the other.

    State = (vehicles on green axis, vehicles on red axis,
             vehicles near the green stop lines, vehicles near the red stop lines,
             green time so far)
    """

    shape = (len(COUNT_EDGES) + 1, len(COUNT_EDGES) + 1, NEAR_CAP + 1, NEAR_CAP + 1,
             len(ELAPSED_EDGES) + 1)

    @staticmethod
    def split(obs):
        """Return (green_count, red_count, green_near, red_near, elapsed) from a raw observation."""
        n, s, e, w, nn, ns, ne, nw, phase, elapsed = (int(x) for x in obs)
        if phase == 0:
            return n + s, e + w, nn + ns, ne + nw, elapsed
        return e + w, n + s, ne + nw, nn + ns, elapsed

    def __call__(self, obs):
        green, red, green_near, red_near, elapsed = self.split(obs)
        return (
            int(np.searchsorted(COUNT_EDGES, green, side="right")),
            int(np.searchsorted(COUNT_EDGES, red, side="right")),
            min(green_near, NEAR_CAP),
            min(red_near, NEAR_CAP),
            int(np.searchsorted(ELAPSED_EDGES, elapsed, side="right")),
        )


class QLearningAgent:
    def __init__(self, n_actions=2, gamma=0.95, alpha_min=0.02, alpha_power=0.7,
                 epsilon=1.0, min_epsilon=0.02, seed=None):
        self.encoder = StateEncoder()
        self.n_actions = n_actions
        self.gamma = gamma
        self.alpha_min = alpha_min
        self.alpha_power = alpha_power
        self.epsilon = epsilon
        self.min_epsilon = min_epsilon
        self.rng = np.random.default_rng(seed)

        # Rewards are always <= 0, so a zero-initialised table is optimistic:
        # untried actions look attractive, which drives systematic exploration.
        self.q_table = np.zeros(self.encoder.shape + (n_actions,))
        self.visits = np.zeros(self.encoder.shape + (n_actions,), dtype=np.int64)

    # ------------------------------------------------------------------ acting
    def act(self, obs, greedy=True):
        """Choose an action for a raw observation."""
        if not greedy and self.rng.random() < self.epsilon:
            return int(self.rng.integers(self.n_actions))
        state = self.encoder(obs)
        if greedy and not self.visits[state].all():
            # A state the agent never properly explored: fall back to a safe
            # actuated-style rule instead of trusting meaningless Q-values.
            green, red, green_near, _, _ = self.encoder.split(obs)
            if red == 0:
                return KEEP
            return SWITCH if green_near == 0 or red > green else KEEP
        q = self.q_table[state]
        if q[0] == q[1]:
            return int(self.rng.integers(self.n_actions))
        return int(np.argmax(q))

    # ---------------------------------------------------------------- learning
    def learn(self, obs, action, reward, next_obs, terminated=False):
        state = self.encoder(obs)
        idx = state + (action,)
        self.visits[idx] += 1
        # Per state-action step size that decays with experience: fast early
        # learning, then averaging out the noise of stochastic arrivals.
        alpha = max(self.alpha_min, 1.0 / self.visits[idx] ** self.alpha_power)
        target = reward
        if not terminated:  # time-limit truncation still bootstraps
            target += self.gamma * np.max(self.q_table[self.encoder(next_obs)])
        self.q_table[idx] += alpha * (target - self.q_table[idx])

    def set_epsilon(self, progress, explore_fraction=0.7):
        """Linear decay from 1.0 to min_epsilon over the first part of training."""
        frac = min(1.0, progress / explore_fraction)
        self.epsilon = 1.0 + frac * (self.min_epsilon - 1.0)

    # ------------------------------------------------------------- persistence
    def save(self, filename):
        np.savez_compressed(
            filename,
            q_table=self.q_table,
            visits=self.visits,
            count_edges=np.array(COUNT_EDGES),
            elapsed_edges=np.array(ELAPSED_EDGES),
            near_cap=np.array(NEAR_CAP),
        )

    def load(self, filename):
        with np.load(filename) as data:
            if (data["q_table"].shape != self.q_table.shape
                    or tuple(data["count_edges"]) != COUNT_EDGES
                    or tuple(data["elapsed_edges"]) != ELAPSED_EDGES
                    or int(data["near_cap"]) != NEAR_CAP):
                raise ValueError(f"{filename} was trained with a different state encoding; retrain it.")
            self.q_table = data["q_table"]
            self.visits = data["visits"]
        self.epsilon = 0.0

    @property
    def coverage(self):
        """Fraction of states where both actions have been tried."""
        return float(self.visits.all(axis=-1).mean())
