"""Compare the trained agent against the baseline controllers.

    python backend/evaluate.py                 # default densities, 10 seeds each
    python backend/evaluate.py --episodes 30 --densities 0.3 0.6 0.9

All controllers face exactly the same traffic (same seeds). The metric is the
average time a vehicle spends waiting, in ticks (lower is better).
"""
import argparse
from pathlib import Path

import numpy as np

from agent import QLearningAgent
from baselines import make_baselines
from traffic_env import TrafficEnv

DEFAULT_MODEL = Path(__file__).resolve().parent.parent / "q_table.npz"
DEFAULT_DENSITIES = (0.2, 0.4, 0.6, 0.8, 1.0)


def run_episode(policy, density, seed, **env_overrides):
    """Run one episode; `policy(env)` returns the action. Returns the final info dict."""
    env = TrafficEnv(**env_overrides)
    env.reset(seed=seed, options={"density": density})
    done = False
    info = {}
    while not done:
        _, _, terminated, truncated, info = env.step(policy(env))
        done = terminated or truncated
    return info


def agent_policy(agent):
    return lambda env: agent.act(env.observe(), greedy=True)


def evaluate(policy, densities=DEFAULT_DENSITIES, episodes=10, seed=10_000, **env_overrides):
    """Mean average-wait per density, plus the standard error."""
    results = {}
    for d in densities:
        waits = [run_episode(policy, d, seed + i, **env_overrides)["avg_wait"] for i in range(episodes)]
        results[d] = (float(np.mean(waits)), float(np.std(waits) / np.sqrt(len(waits))))
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--model", default=str(DEFAULT_MODEL))
    parser.add_argument("--episodes", type=int, default=10)
    parser.add_argument("--densities", type=float, nargs="+", default=list(DEFAULT_DENSITIES))
    parser.add_argument("--seed", type=int, default=10_000)
    args = parser.parse_args()

    policies = make_baselines()
    try:
        agent = QLearningAgent()
        agent.load(args.model)
        policies["q_learning"] = agent_policy(agent)
    except FileNotFoundError:
        print(f"No model at {args.model}; evaluating baselines only (run train.py first).\n")

    table = {name: evaluate(p, args.densities, args.episodes, args.seed) for name, p in policies.items()}

    print(f"Average wait per vehicle in ticks ({args.episodes} episodes per cell, lower is better)\n")
    header = f"{'controller':<15}" + "".join(f"{'d=' + str(d):>14}" for d in args.densities) + f"{'mean':>9}"
    print(header)
    print("-" * len(header))
    for name, res in table.items():
        cells = "".join(f"{res[d][0]:>8.1f} ±{res[d][1]:<4.1f}" for d in args.densities)
        print(f"{name:<15}{cells}{np.mean([res[d][0] for d in args.densities]):>9.1f}")


if __name__ == "__main__":
    main()
