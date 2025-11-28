import gymnasium as gym
from gymnasium import spaces
import numpy as np

class Car:
    def __init__(self, lane, position=0):
        self.id = np.random.randint(0, 1000000)
        self.lane = lane # 0: N, 1: S, 2: E, 3: W
        self.position = position # 0 to 100 (100 is stop line)
        self.speed = 0
        self.max_speed = 2.0 # Units per tick
        self.length = 5.0 # Car length
        self.waiting = False

class MockTrafficEnv(gym.Env):
    """
    Physics-based mock traffic environment.
    Tracks individual cars.
    """
    
    def __init__(self):
        super(MockTrafficEnv, self).__init__()
        
        # Actions: 0 (Keep), 1 (Switch)
        self.action_space = spaces.Discrete(2)
        
        # Observation: [North_Q, South_Q, East_Q, West_Q, Phase]
        # Discretized: 0 (Low), 1 (Medium), 2 (High)
        self.observation_space = spaces.MultiDiscrete([3, 3, 3, 3, 2])
        
        self.lanes = [[], [], [], []] # Lists of Car objects for N, S, E, W
        self.phase = 0 # 0: NS Green, 1: EW Green
        self.steps_in_phase = 0
        self.min_phase_duration = 10 # Minimum 10 steps (10 seconds) per phase
        self.arrival_prob = 0.3 # Default density
        
        self.max_steps = 1000
        self.current_step = 0
        self.stop_line = 100.0
        
    def set_density(self, density):
        # density: 0.0 to 1.0
        self.arrival_prob = max(0.05, min(0.8, density))
        
    def _get_obs(self):
        # Calculate queue lengths (cars with speed < 0.1)
        queues = []
        for lane_cars in self.lanes:
            q_count = sum(1 for c in lane_cars if c.speed < 0.5 and c.position > 10)
            queues.append(q_count)
            
        n_q, s_q, e_q, w_q = queues
        
        def discretize(val):
            if val < 5: return 0
            elif val < 10: return 1
            else: return 2
            
        return np.array([
            discretize(n_q),
            discretize(s_q),
            discretize(e_q),
            discretize(w_q),
            self.phase
        ], dtype=np.int32)

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        self.lanes = [[], [], [], []]
        self.phase = np.random.randint(0, 2)
        self.steps_in_phase = 0
        self.current_step = 0
        
        # Spawn some initial cars
        for i in range(4):
            num_cars = np.random.randint(0, 5)
            for j in range(num_cars):
                # Spawn at different positions
                pos = self.stop_line - (j * 10.0) - 5.0
                if pos > 0:
                    self.lanes[i].append(Car(i, pos))
                    
        return self._get_obs(), {}
        
    def step(self, action):
        self.current_step += 1
        self.steps_in_phase += 1
        
        # 1. Action (with constraints)
        # Only allow switch if min duration passed
        if action == 1 and self.steps_in_phase >= self.min_phase_duration:
            self.phase = 1 - self.phase
            self.steps_in_phase = 0
            
        # 2. Spawn Cars
        # Prob self.arrival_prob per lane per tick
        for i in range(4):
            if np.random.rand() < self.arrival_prob:
                # Check if start is clear
                if not self.lanes[i] or self.lanes[i][-1].position > 15:
                    self.lanes[i].append(Car(i, 0))
                    
        # 3. Move Cars
        for lane_idx, cars in enumerate(self.lanes):
            # Determine if light is green for this lane
            is_green = False
            if self.phase == 0 and lane_idx in [0, 1]: is_green = True
            if self.phase == 1 and lane_idx in [2, 3]: is_green = True
            
            cars_to_remove = []
            
            for i, car in enumerate(cars):
                # Calculate target speed
                target_speed = car.max_speed
                
                # Distance to car ahead
                dist_to_next = 1000.0
                if i > 0: # There is a car ahead
                    dist_to_next = cars[i-1].position - car.position - car.length
                
                # Distance to stop line
                dist_to_stop = self.stop_line - car.position
                
                # Logic
                # Increase safety distance to 10.0
                if dist_to_next < 10.0:
                    target_speed = 0 # Stop if too close to car ahead
                elif not is_green and dist_to_stop < 10.0 and dist_to_stop > 0:
                     # Red light and BEFORE stop line. 
                     # If dist_to_stop <= 0, we are already past the line, so KEEP GOING to clear intersection.
                     target_speed = 0
                
                # Accelerate/Decelerate
                if car.speed < target_speed:
                    car.speed += 0.2
                elif car.speed > target_speed:
                    car.speed -= 0.5 # Brake harder
                    
                car.speed = max(0, min(car.speed, car.max_speed))
                
                # Move
                car.position += car.speed
                
                # Remove if crossed intersection (e.g. pos > 100)
                # User requested immediate removal at stop line to avoid collisions
                if car.position > 100:
                    cars_to_remove.append(car)
            
            for c in cars_to_remove:
                cars.remove(c)
                
        # 4. Reward
        # Negative count of waiting cars (speed < 0.1)
        total_waiting = 0
        for cars in self.lanes:
            total_waiting += sum(1 for c in cars if c.speed < 0.5 and c.position < self.stop_line)
            
        reward = -total_waiting
        
        terminated = self.current_step >= self.max_steps
        truncated = False
        
        return self._get_obs(), reward, terminated, truncated, {}
