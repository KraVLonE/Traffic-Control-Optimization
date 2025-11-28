import asyncio
import json
import numpy as np
from mock_env import MockTrafficEnv
from agent import QLearningAgent

class Simulation:
    def __init__(self, model_path="q_table.pkl"):
        self.env = MockTrafficEnv()
        # State space shape: (3, 3, 3, 3, 2)
        state_space_shape = (3, 3, 3, 3, 2)
        action_space_size = self.env.action_space.n
        
        self.agent = QLearningAgent(action_space_size, state_space_shape)
        try:
            self.agent.load(model_path)
            print("Loaded trained model.")
        except FileNotFoundError:
            print("No trained model found, using random agent.")
            
        self.running = False
        self.paused = False
        self.current_obs = None
        
        # Metrics Tracking
        self.total_queue_sum = 0
        self.total_steps = 0
        self.history = [] # Store last 50 data points for graph
        
    def reset(self):
        self.current_obs, _ = self.env.reset()
        self.total_queue_sum = 0
        self.total_steps = 0
        self.history = []
        
    async def handle_command(self, command):
        cmd_type = command.get("type")
        if cmd_type == "start":
            self.paused = False
        elif cmd_type == "stop":
            self.paused = True
        elif cmd_type == "reset":
            self.reset()
        elif cmd_type == "set_density":
            val = float(command.get("value", 0.3))
            self.env.set_density(val)
            
    async def run_loop(self, websocket):
        self.running = True
        self.paused = False
        self.reset()
        
        # Start simulation loop as a background task
        sim_task = asyncio.create_task(self._simulation_loop(websocket))
        
        try:
            while self.running:
                # Wait for commands from client
                data = await websocket.receive_text()
                command = json.loads(data)
                await self.handle_command(command)
        except Exception as e:
            print(f"WebSocket connection closed: {e}")
        finally:
            self.running = False
            sim_task.cancel()
            try:
                await sim_task
            except asyncio.CancelledError:
                pass

    async def _simulation_loop(self, websocket):
        while self.running:
            if not self.paused:
                # 1. Agent chooses action
                # Use exploitation (epsilon=0) for simulation
                action = np.argmax(self.agent.q_table[tuple(self.current_obs)])
                
                # 2. Step environment
                next_obs, reward, terminated, truncated, _ = self.env.step(action)
                self.current_obs = next_obs
                
                # Update Metrics only when running
                n_q = sum(1 for c in self.env.lanes[0] if c.speed < 0.5)
                s_q = sum(1 for c in self.env.lanes[1] if c.speed < 0.5)
                e_q = sum(1 for c in self.env.lanes[2] if c.speed < 0.5)
                w_q = sum(1 for c in self.env.lanes[3] if c.speed < 0.5)
                current_total_queue = n_q + s_q + e_q + w_q
                
                self.total_steps += 1
                self.total_queue_sum += current_total_queue
                
                self.history.append(current_total_queue)
                if len(self.history) > 20:
                    self.history.pop(0)
                
                if terminated or truncated:
                    self.reset()

            # 3. Get detailed state for visualization (ALWAYS run this to update UI)
            # Extract car positions
            vehicles = []
            for lane_idx, cars in enumerate(self.env.lanes):
                for car in cars:
                    vehicles.append({
                        "id": car.id,
                        "lane": lane_idx, # 0:N, 1:S, 2:E, 3:W
                        "position": car.position, # 0-150
                        "speed": car.speed
                    })
            
            # Calculate metrics for display
            n_q = sum(1 for c in self.env.lanes[0] if c.speed < 0.5)
            s_q = sum(1 for c in self.env.lanes[1] if c.speed < 0.5)
            e_q = sum(1 for c in self.env.lanes[2] if c.speed < 0.5)
            w_q = sum(1 for c in self.env.lanes[3] if c.speed < 0.5)
            phase = self.env.phase
            current_total_queue = n_q + s_q + e_q + w_q
            
            # Avoid division by zero
            avg_wait_time = 0
            if self.total_steps > 0:
                avg_queue_length = self.total_queue_sum / self.total_steps
                avg_wait_time = avg_queue_length / 1.2 
            
            state_data = {
                "vehicles": vehicles,
                "lights": {
                    "north_south": "green" if phase == 0 else "red",
                    "east_west": "red" if phase == 0 else "green"
                },
                "metrics": {
                    "total_queue": current_total_queue,
                    "avg_wait_time": round(avg_wait_time, 1),
                    "step": self.env.current_step,
                    "history": self.history
                }
            }
            
            # 4. Send to client
            try:
                await websocket.send_text(json.dumps(state_data))
            except Exception:
                break
            
            # 5. Wait for next tick (e.g., 0.1 second per step for smooth physics)
            await asyncio.sleep(0.1)
