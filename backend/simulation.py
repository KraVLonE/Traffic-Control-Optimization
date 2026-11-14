"""Live simulation session: steps the environment and streams state over a WebSocket."""
import asyncio
import json
from collections import deque

from fastapi import WebSocketDisconnect

from baselines import make_baselines
from traffic_env import EW, NS, TrafficEnv

TICK_SECONDS = 0.1          # wall-clock time per simulation tick at speed 1x
HISTORY_POINTS = 60
HISTORY_SAMPLE_TICKS = 5
THROUGHPUT_WINDOW = 300     # ticks


class Simulation:
    """One independent simulation per connected client."""

    def __init__(self, agent=None):
        # Live view runs indefinitely; episodes only matter for training.
        self.env = TrafficEnv(episode_ticks=10**12)
        self.controllers = make_baselines()
        if agent is not None:
            self.controllers = {"q_learning": lambda env: agent.act(env.observe(), greedy=True),
                                **self.controllers}
        self.controller_name = next(iter(self.controllers))
        self.paused = False
        self.speed = 1.0
        self.history = deque(maxlen=HISTORY_POINTS)
        self.crossings = deque()   # (tick, completed_total) samples for throughput
        self.reset()

    def reset(self):
        self.env.reset()
        self.history.clear()
        self.crossings.clear()

    def handle_command(self, command):
        cmd_type = command.get("type")
        value = command.get("value")
        if cmd_type == "start":
            self.paused = False
        elif cmd_type == "stop":
            self.paused = True
        elif cmd_type == "reset":
            self.reset()
        elif cmd_type == "set_density":
            self.env.set_density(float(value))
        elif cmd_type == "set_controller" and value in self.controllers:
            self.controller_name = value
        elif cmd_type == "set_speed":
            self.speed = min(8.0, max(0.25, float(value)))

    def advance(self):
        """One simulation tick under the selected controller."""
        env = self.env
        if env.decision_due:
            env.apply_action(self.controllers[self.controller_name](env))
        env.tick()

        if env.tick_count % HISTORY_SAMPLE_TICKS == 0:
            self.history.append(env.waiting)
        self.crossings.append((env.tick_count, env.completed))
        while self.crossings[0][0] < env.tick_count - THROUGHPUT_WINDOW:
            self.crossings.popleft()

    def snapshot(self):
        env = self.env
        first_tick, first_done = self.crossings[0] if self.crossings else (env.tick_count, env.completed)
        window = env.tick_count - first_tick
        throughput = (env.completed - first_done) * 60 / window if window else 0.0
        return {
            "vehicles": [
                {"id": car.id, "lane": lane, "sublane": car.sublane, "kind": car.kind,
                 "length": car.length, "position": round(car.position, 2), "speed": round(car.speed, 2)}
                for lane in range(4) for car in env.approach_cars(lane)
            ],
            "lanes_per_approach": env.cfg.lanes_per_approach,
            "lights": {"north_south": env.light(NS), "east_west": env.light(EW)},
            "backlog": [len(b) for b in env.backlog],
            "metrics": {
                "total_queue": env.waiting,
                "lane_queues": env.lane_queues(),
                # Mean waiting time per vehicle so far (1 tick = 1 simulated second).
                "avg_wait_time": round(env.total_wait_ticks / env.arrived, 1) if env.arrived else 0.0,
                "throughput": round(throughput, 1),   # vehicles per simulated minute
                "completed": env.completed,
                "step": env.tick_count,
                "history": list(self.history),
            },
            "controller": self.controller_name,
            "controllers": list(self.controllers),
            "density": env.density,
            "speed": self.speed,
            "paused": self.paused,
        }

    async def run(self, websocket):
        sender = asyncio.create_task(self._send_loop(websocket))
        try:
            while True:
                data = await websocket.receive_text()
                try:
                    self.handle_command(json.loads(data))
                except (ValueError, TypeError, AttributeError):
                    continue  # ignore malformed commands
        except WebSocketDisconnect:
            pass
        finally:
            sender.cancel()
            try:
                await sender
            except asyncio.CancelledError:
                pass

    async def _send_loop(self, websocket):
        while True:
            if not self.paused:
                self.advance()
            try:
                await websocket.send_text(json.dumps(self.snapshot()))
            except (WebSocketDisconnect, RuntimeError):
                return
            await asyncio.sleep(TICK_SECONDS / self.speed)
