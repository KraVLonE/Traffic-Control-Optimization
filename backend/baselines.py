"""Hand-written signal controllers used as baselines for the RL agent.

Every controller is a callable `policy(env) -> action` (0 = keep, 1 = switch).
"""
from traffic_env import KEEP, SWITCH, lane_axis


class FixedCycle:
    """Switch after a fixed green time, regardless of traffic."""

    def __init__(self, green_ticks=30):
        self.green_ticks = green_ticks

    def __call__(self, env):
        return SWITCH if env.green_elapsed >= self.green_ticks else KEEP


class LongestQueue:
    """Give green to the axis with more vehicles (greedy max-pressure)."""

    def __init__(self, margin=0):
        self.margin = margin

    def __call__(self, env):
        counts = env.axis_counts()
        return SWITCH if counts[1 - env.phase] > counts[env.phase] + self.margin else KEEP


class Actuated:
    """Classic vehicle-actuated control: hold green while cars are still arriving
    at the stop line, switch when the green approach runs dry (gap-out) or the
    maximum green is reached, provided someone is waiting on the other axis."""

    def __init__(self, detect_distance=20.0, max_green=60):
        self.detect_distance = detect_distance
        self.max_green = max_green

    def __call__(self, env):
        if env.axis_counts()[1 - env.phase] == 0:
            return KEEP
        if env.green_elapsed >= self.max_green:
            return SWITCH
        line = env.cfg.lane_length
        for lane in range(4):
            if lane_axis(lane) != env.phase:
                continue
            for cars in env.lanes[lane]:
                if cars and line - cars[0].position <= self.detect_distance:
                    return KEEP
        return SWITCH


def make_baselines():
    return {
        "fixed_20": FixedCycle(20),
        "fixed_40": FixedCycle(40),
        "longest_queue": LongestQueue(),
        "actuated": Actuated(),
    }
