"""Single 4-way intersection traffic environment (Gymnasium API).

Time is measured in ticks (1 tick = 1 simulated second). The controller makes
one decision every `decision_interval` ticks: keep the current green, or
switch (yellow -> all-red -> other axis green).

Approaches: 0 = North, 1 = South, 2 = East, 3 = West. Each approach has
`lanes_per_approach` parallel lanes and carries a mix of bikes, cars and trucks.
Axes / phases: 0 = North-South green, 1 = East-West green.
"""
from collections import deque
from dataclasses import dataclass
import math

import gymnasium as gym
from gymnasium import spaces
import numpy as np

NS, EW = 0, 1

# kind: (length, max speed, acceleration) in units and units per tick
VEHICLE_TYPES = {
    "bike": (3.0, 2.2, 0.30),
    "car": (6.0, 2.0, 0.20),
    "truck": (12.0, 1.6, 0.12),
}
LANE_NAMES = ("north", "south", "east", "west")
KEEP, SWITCH = 0, 1


def lane_axis(lane):
    return NS if lane < 2 else EW


@dataclass
class EnvConfig:
    # Geometry / vehicle dynamics (units per tick)
    lane_length: float = 100.0     # stop line position
    lanes_per_approach: int = 2
    vehicle_mix: tuple = (("bike", 0.25), ("car", 0.60), ("truck", 0.15))
    min_gap: float = 2.0           # bumper-to-bumper gap when stopped
    stop_margin: float = 0.5       # cars stop this far before the line
    decel: float = 0.5             # comfortable braking
    wait_speed: float = 0.5        # below this a car counts as waiting
    detect_distance: float = 25.0  # stop-line detector range

    # Signal timing (ticks)
    decision_interval: int = 5
    yellow_ticks: int = 4
    all_red_ticks: int = 1
    min_green: int = 10
    max_green: int = 120           # forced switch if cross traffic is present

    # Demand
    capacity_rate: float = 0.15    # arrivals/approach/tick at density 1.0 (~saturation)
    density: float = 0.5           # demand as a fraction of capacity
    max_imbalance: float = 0.5     # NS/EW demand split varies by +-this
    lane_jitter: float = 0.15      # per-lane variation on top of the axis split
    demand_shift_interval: int = 450  # ticks between demand pattern changes
    max_backlog: int = 40          # vehicles queued upstream of the visible road, per approach

    episode_ticks: int = 1800


class Car:
    """A vehicle of any kind (bike, car or truck)."""

    __slots__ = ("id", "lane", "sublane", "kind", "length", "max_speed", "accel",
                 "position", "speed", "wait", "committed")

    def __init__(self, car_id, lane, sublane, kind, speed, wait):
        self.id = car_id
        self.lane = lane        # approach index
        self.sublane = sublane  # 0 = next to the centre line
        self.kind = kind
        self.length, self.max_speed, self.accel = VEHICLE_TYPES[kind]
        self.position = 0.0     # front bumper; lane_length is the stop line
        self.speed = min(speed, self.max_speed)
        self.wait = wait        # ticks spent waiting so far
        self.committed = False  # passed the point of no return on yellow


class TrafficEnv(gym.Env):
    metadata = {"render_modes": []}

    def __init__(self, config=None, **overrides):
        super().__init__()
        self.cfg = config or EnvConfig()
        for key, value in overrides.items():
            if not hasattr(self.cfg, key):
                raise TypeError(f"Unknown config field: {key}")
            setattr(self.cfg, key, value)

        self.action_space = spaces.Discrete(2)
        # [vehicles on N, S, E, W approach (incl. upstream backlog),
        #  vehicles within detect_distance of the N, S, E, W stop lines,
        #  phase, green_elapsed]
        self._kinds = [k for k, _ in self.cfg.vehicle_mix]
        shares = np.array([p for _, p in self.cfg.vehicle_mix], dtype=float)
        self._kind_probs = shares / shares.sum()
        high = np.full(10, np.iinfo(np.int32).max, dtype=np.int32)
        high[8] = 1
        self.observation_space = spaces.Box(low=np.zeros(10, dtype=np.int32), high=high, dtype=np.int32)

        self.density = self.cfg.density
        self._reset_state()

    # ------------------------------------------------------------------ setup
    def _reset_state(self):
        # lanes[approach][sublane] -> vehicles ordered front (near the line) to back
        self.lanes = [[[] for _ in range(self.cfg.lanes_per_approach)] for _ in range(4)]
        # (arrival tick, kind) of vehicles that have not entered the visible road yet
        self.backlog = [deque() for _ in range(4)]
        self.phase = NS
        self.green_elapsed = 0
        self.transition_remaining = 0             # >0 while in yellow / all-red
        self.tick_count = 0
        self._ticks_since_decision = 0
        self._next_car_id = 0
        self.lane_weights = np.ones(4)

        # Statistics
        self.waiting = 0             # vehicles waiting right now
        self.total_wait_ticks = 0    # vehicle-ticks of waiting, all vehicles
        self.arrived = 0
        self.completed = 0
        self.completed_wait = 0      # total wait of vehicles that crossed
        self.dropped = 0             # arrivals rejected because backlog was full
        self.switches = 0

    def set_density(self, density):
        self.density = float(min(1.5, max(0.0, density)))

    def _sample_demand(self):
        cfg = self.cfg
        split = self.np_random.uniform(-cfg.max_imbalance, cfg.max_imbalance)
        axis = np.array([1 + split, 1 + split, 1 - split, 1 - split])
        jitter = self.np_random.uniform(1 - cfg.lane_jitter, 1 + cfg.lane_jitter, size=4)
        self.lane_weights = axis * jitter

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        self._reset_state()
        if options and "density" in options:
            self.set_density(options["density"])
        self.phase = int(self.np_random.integers(2))
        self._sample_demand()
        return self.observe(), self._info()

    # ------------------------------------------------------------ observation
    def approach_cars(self, approach):
        """All vehicles on an approach, across its lanes."""
        return [car for sub in self.lanes[approach] for car in sub]

    def lane_counts(self):
        """Vehicles on each approach, including the upstream backlog."""
        return [sum(len(sub) for sub in self.lanes[i]) + len(self.backlog[i]) for i in range(4)]

    def lane_queues(self):
        """Vehicles currently waiting on each approach."""
        ws = self.cfg.wait_speed
        return [sum(1 for sub in self.lanes[i] for c in sub if c.speed < ws) + len(self.backlog[i])
                for i in range(4)]

    def axis_counts(self):
        n, s, e, w = self.lane_counts()
        return n + s, e + w

    def lane_near(self):
        """Vehicles within detect_distance of each stop line (a loop detector)."""
        start = self.cfg.lane_length - self.cfg.detect_distance
        return [sum(1 for sub in self.lanes[i] for c in sub if c.position >= start) for i in range(4)]

    def observe(self):
        return np.array(
            self.lane_counts() + self.lane_near() + [self.phase, self.green_elapsed], dtype=np.int32
        )

    def light(self, axis):
        if axis != self.phase:
            return "red"
        if self.transition_remaining == 0:
            return "green"
        return "yellow" if self.transition_remaining > self.cfg.all_red_ticks else "red"

    @property
    def can_switch(self):
        return self.transition_remaining == 0 and self.green_elapsed >= self.cfg.min_green

    @property
    def decision_due(self):
        return self.transition_remaining == 0 and self._ticks_since_decision >= self.cfg.decision_interval

    def _info(self):
        return {
            "waiting": self.waiting,
            "arrived": self.arrived,
            "completed": self.completed,
            "dropped": self.dropped,
            "switches": self.switches,
            "total_wait_ticks": self.total_wait_ticks,
            "avg_wait": self.total_wait_ticks / self.arrived if self.arrived else 0.0,
            "action_mask": np.array([1, int(self.can_switch)], dtype=np.int8),
        }

    # ----------------------------------------------------------------- control
    def apply_action(self, action):
        """Register a controller decision. Returns True if a switch started."""
        self._ticks_since_decision = 0
        if self.transition_remaining > 0:
            return False
        want_switch = action == SWITCH and self.green_elapsed >= self.cfg.min_green
        if not want_switch and self.green_elapsed >= self.cfg.max_green:
            want_switch = self.axis_counts()[1 - self.phase] > 0
        if not want_switch:
            return False

        cfg = self.cfg
        self.transition_remaining = cfg.yellow_ticks + cfg.all_red_ticks
        self.switches += 1
        # Cars too close to stop comfortably run the yellow.
        for lane in range(4):
            if lane_axis(lane) != self.phase:
                continue
            for car in self.approach_cars(lane):
                dist = cfg.lane_length - cfg.stop_margin - car.position
                car.committed = dist < car.speed ** 2 / (2 * cfg.decel)
        return True

    def tick(self):
        """Advance the simulation by one tick. Returns the number of waiting vehicles."""
        cfg = self.cfg
        self.tick_count += 1
        self._ticks_since_decision += 1
        rng = self.np_random

        # Signal
        if self.transition_remaining > 0:
            self.transition_remaining -= 1
            if self.transition_remaining == 0:
                self.phase = 1 - self.phase
                self.green_elapsed = 0
        else:
            self.green_elapsed += 1

        # Demand
        if cfg.demand_shift_interval and self.tick_count % cfg.demand_shift_interval == 0:
            self._sample_demand()
        rates = self.density * cfg.capacity_rate * self.lane_weights
        arrivals = rng.random(4) < rates

        waiting = 0
        stop_at = cfg.lane_length - cfg.stop_margin
        two_b = 2 * cfg.decel
        for lane in range(4):
            backlog = self.backlog[lane]

            if arrivals[lane]:
                if len(backlog) < cfg.max_backlog:
                    kind = self._kinds[int(rng.choice(len(self._kinds), p=self._kind_probs))]
                    backlog.append((self.tick_count, kind))
                    self.arrived += 1
                else:
                    self.dropped += 1

            green = self.transition_remaining == 0 and lane_axis(lane) == self.phase

            for cars in self.lanes[lane]:
                # Move vehicles, front to back
                crossed = 0
                leader = None
                for car in cars:
                    v = min(car.speed + car.accel, car.max_speed)
                    if leader is not None:
                        gap = leader.position - leader.length - cfg.min_gap - car.position
                        if gap < 0.05:
                            v = 0.0
                        else:
                            v = min(v, gap, math.sqrt(two_b * gap + leader.speed ** 2))
                    if not green and not car.committed:
                        dist = stop_at - car.position
                        v = min(v, dist, math.sqrt(two_b * dist)) if dist >= 0.05 else 0.0
                    car.speed = v
                    car.position += v
                    if v < cfg.wait_speed:
                        car.wait += 1
                        waiting += 1
                    if car.position >= cfg.lane_length:
                        crossed += 1
                        self.completed += 1
                        self.completed_wait += car.wait
                    else:
                        leader = car
                if crossed:
                    del cars[:crossed]

            # Let backlog vehicles onto the road: each takes the lane with the most room,
            # at most one vehicle per lane per tick.
            free = list(range(cfg.lanes_per_approach))
            while backlog and free:
                def room(sub):
                    cars = self.lanes[lane][sub]
                    return cars[-1].position - cars[-1].length - cfg.min_gap if cars else cfg.lane_length
                sub = max(free, key=room)
                gap = room(sub)
                if gap <= 0:
                    break
                cars = self.lanes[lane][sub]
                lead_speed = cars[-1].speed if cars else 0.0
                arrival_tick, kind = backlog.popleft()
                speed = min(gap, math.sqrt(two_b * gap + lead_speed ** 2))
                cars.append(Car(self._next_car_id, lane, sub, kind, speed, self.tick_count - arrival_tick))
                self._next_car_id += 1
                free.remove(sub)
            waiting += len(backlog)

        self.waiting = waiting
        self.total_wait_ticks += waiting
        return waiting

    def step(self, action):
        """One controller decision: apply the action, then simulate until the next decision."""
        self.apply_action(action)
        total_waiting = 0
        while True:
            total_waiting += self.tick()
            if self.decision_due:
                break
        # Mean number of waiting vehicles per tick, scaled to the decision interval,
        # so a switch (which takes at least as long) is charged for its full duration.
        reward = -total_waiting / self.cfg.decision_interval
        truncated = self.tick_count >= self.cfg.episode_ticks
        return self.observe(), reward, False, truncated, self._info()
