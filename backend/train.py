"""Train the Q-learning traffic signal agent.

    python backend/train.py                    # full run: 10000 episodes, ~15 min
    python backend/train.py --episodes 2000    # quick run

Each episode uses a random traffic density so the agent learns a policy that
works from light to saturated traffic. Every `--eval-every` episodes the greedy
policy is scored on a fixed set of evaluation seeds, and the best table so far
is saved.
"""
import argparse
import csv
from pathlib import Path

import numpy as np

from agent import QLearningAgent
from evaluate import DEFAULT_DENSITIES, DEFAULT_MODEL, agent_policy, evaluate
from traffic_env import TrafficEnv


def train(episodes=10000, seed=0, out=DEFAULT_MODEL, eval_every=1000, eval_episodes=6,
          density_range=(0.15, 1.1), log_path=None, verbose=True):
    rng = np.random.default_rng(seed)
    env = TrafficEnv()
    agent = QLearningAgent(seed=seed)
    best_score = float("inf")
    log = []

    for episode in range(episodes):
        agent.set_epsilon(episode / episodes)
        density = float(rng.uniform(*density_range))
        obs, _ = env.reset(seed=int(rng.integers(2**31)), options={"density": density})
        done = False
        while not done:
            action = agent.act(obs, greedy=False)
            next_obs, reward, terminated, truncated, _ = env.step(action)
            agent.learn(obs, action, reward, next_obs, terminated)
            obs = next_obs
            done = terminated or truncated

        if (episode + 1) % eval_every == 0 or episode + 1 == episodes:
            results = evaluate(agent_policy(agent), DEFAULT_DENSITIES, eval_episodes, seed=50_000)
            score = float(np.mean([m for m, _ in results.values()]))
            log.append({"episode": episode + 1, "epsilon": round(agent.epsilon, 3),
                        "coverage": round(agent.coverage, 3), "avg_wait": round(score, 2)})
            saved = ""
            if score < best_score:
                best_score = score
                agent.save(out)
                saved = "  (saved)"
            if verbose:
                print(f"episode {episode + 1:>5}/{episodes}  eps {agent.epsilon:.2f}  "
                      f"coverage {agent.coverage:.0%}  eval avg wait {score:6.2f}{saved}")

    if log_path:
        with open(log_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(log[0]))
            writer.writeheader()
            writer.writerows(log)
    if verbose:
        print(f"\nBest eval avg wait: {best_score:.2f} ticks. Model saved to {out}")
        print("Run `python backend/evaluate.py` to compare against the baselines.")
    return agent, log


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--episodes", type=int, default=10000)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--out", default=str(DEFAULT_MODEL))
    parser.add_argument("--eval-every", type=int, default=1000)
    parser.add_argument("--log", default=str(Path(DEFAULT_MODEL).with_name("training_log.csv")))
    args = parser.parse_args()
    train(args.episodes, args.seed, args.out, args.eval_every, log_path=args.log)


if __name__ == "__main__":
    main()
