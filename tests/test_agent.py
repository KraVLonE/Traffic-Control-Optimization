import numpy as np
import pytest

from agent import QLearningAgent, StateEncoder
from traffic_env import KEEP, SWITCH, TrafficEnv


def test_encoder_is_phase_symmetric():
    enc = StateEncoder()
    ns_green = np.array([3, 2, 7, 1, 1, 0, 2, 0, 0, 12])
    ew_green = np.array([7, 1, 3, 2, 2, 0, 1, 0, 1, 12])
    assert enc(ns_green) == enc(ew_green)
    assert all(0 <= s < n for s, n in zip(enc(ns_green), enc.shape))


def test_encoder_handles_extreme_values():
    enc = StateEncoder()
    state = enc(np.array([99, 99, 99, 99, 50, 50, 50, 50, 1, 10**6]))
    assert all(0 <= s < n for s, n in zip(state, enc.shape))


def test_learn_moves_q_towards_target():
    agent = QLearningAgent(seed=0)
    obs = np.array([1, 0, 4, 0, 0, 0, 1, 0, 0, 20])
    agent.learn(obs, SWITCH, -3.0, obs, terminated=True)
    assert agent.q_table[agent.encoder(obs) + (SWITCH,)] == pytest.approx(-3.0)


def test_unexplored_state_falls_back_to_longest_queue():
    agent = QLearningAgent(seed=0)
    assert agent.act(np.array([0, 0, 5, 5, 0, 0, 2, 2, 0, 30])) == SWITCH
    assert agent.act(np.array([5, 5, 0, 0, 2, 2, 0, 0, 0, 30])) == KEEP


def test_save_load_roundtrip(tmp_path):
    agent = QLearningAgent(seed=0)
    env = TrafficEnv(episode_ticks=200)
    obs, _ = env.reset(seed=0)
    for _ in range(30):
        action = agent.act(obs, greedy=False)
        nxt, reward, term, trunc, _ = env.step(action)
        agent.learn(obs, action, reward, nxt, term)
        obs = nxt
    path = tmp_path / "q.npz"
    agent.save(path)
    loaded = QLearningAgent()
    loaded.load(path)
    assert np.array_equal(loaded.q_table, agent.q_table)
    assert np.array_equal(loaded.visits, agent.visits)
