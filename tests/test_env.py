import numpy as np
import pytest

from baselines import make_baselines
from traffic_env import KEEP, SWITCH, TrafficEnv


def rollout(policy, density, seed, ticks=1500):
    env = TrafficEnv(episode_ticks=ticks)
    env.reset(seed=seed, options={"density": density})
    done = False
    while not done:
        _, _, _, done, info = env.step(policy(env))
    return env, info


def test_same_seed_is_deterministic():
    policy = make_baselines()["actuated"]
    _, a = rollout(policy, 0.7, seed=3)
    _, b = rollout(policy, 0.7, seed=3)
    assert a["total_wait_ticks"] == b["total_wait_ticks"]
    assert a["completed"] == b["completed"]


def test_density_controls_arrivals():
    policy = make_baselines()["fixed_20"]
    arrived = [rollout(policy, d, seed=1)[1]["arrived"] for d in (0.2, 0.5, 0.9)]
    assert arrived[0] < arrived[1] < arrived[2]
    # density 0.5 -> 0.5 * capacity_rate arrivals per lane per tick, on average
    assert arrived[1] == pytest.approx(0.5 * TrafficEnv().cfg.capacity_rate * 4 * 1500, rel=0.2)


@pytest.mark.parametrize("name", ["fixed_20", "longest_queue", "actuated"])
def test_cars_never_overlap_or_run_red(name):
    policy = make_baselines()[name]
    env = TrafficEnv(episode_ticks=2000)
    env.reset(seed=7, options={"density": 1.0})
    kinds = set()
    for _ in range(2000):
        if env.decision_due:
            env.apply_action(policy(env))
        before = env.completed
        lights = [env.light(axis) for axis in (0, 1)]
        env.tick()
        for approach in env.lanes:
            for cars in approach:
                kinds.update(c.kind for c in cars)
                for lead, follow in zip(cars, cars[1:]):
                    assert lead.position - lead.length - follow.position >= env.cfg.min_gap - 1e-9
        if env.completed > before:
            # someone crossed: an approach must have been green or yellow just before/after
            assert any(l != "red" for l in lights + [env.light(0), env.light(1)])
    assert kinds == {"bike", "car", "truck"}
    assert all(any(sub for sub in approach) for approach in env.lanes)


def test_vehicles_use_every_lane_and_respect_their_speed_limit():
    env = TrafficEnv(episode_ticks=600)
    env.reset(seed=2, options={"density": 0.9})
    used = set()
    for _ in range(600):
        if env.decision_due:
            env.apply_action(KEEP)
        env.tick()
        for approach in range(4):
            for car in env.approach_cars(approach):
                used.add((approach, car.sublane))
                assert car.speed <= car.max_speed + 1e-9
    assert len(used) == 4 * env.cfg.lanes_per_approach


def test_min_green_blocks_early_switch():
    env = TrafficEnv()
    env.reset(seed=0)
    phase = env.phase
    assert not env.apply_action(SWITCH)          # green_elapsed == 0
    while env.green_elapsed < env.cfg.min_green:
        env.tick()
    assert env.apply_action(SWITCH)
    assert env.light(phase) == "yellow"
    for _ in range(env.cfg.yellow_ticks + env.cfg.all_red_ticks):
        env.tick()
    assert env.phase == 1 - phase and env.light(env.phase) == "green"


def test_reward_is_negative_waiting_and_time_limit_truncates():
    env = TrafficEnv(episode_ticks=50)
    env.reset(seed=0, options={"density": 1.0})
    terminated = truncated = False
    while not truncated:
        obs, reward, terminated, truncated, info = env.step(KEEP)
        assert reward <= 0
        assert env.observation_space.contains(obs)
    assert not terminated
    assert info["total_wait_ticks"] > 0


def test_wait_accounting_matches_per_car_waits():
    env, info = rollout(make_baselines()["fixed_20"], 0.6, seed=5)
    in_system = sum(c.wait for approach in range(4) for c in env.approach_cars(approach))
    in_backlog = sum(env.tick_count - t for b in env.backlog for t, _ in b)
    assert info["total_wait_ticks"] == env.completed_wait + in_system + in_backlog
