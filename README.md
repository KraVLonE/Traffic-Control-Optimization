# Traffic AI Optimization Agent

![Traffic Control Optimization](https://via.placeholder.com/800x400?text=Traffic+AI+Simulation+Dashboard)

A Reinforcement Learning (Q-Learning) project that optimizes traffic flow at a 4-way intersection. The agent learns when to switch the lights to minimize the time vehicles spend waiting, and is benchmarked against classic signal controllers.

## Features

-   **Reinforcement Learning Agent**: Tabular Q-Learning on a compact, phase-symmetric state (vehicles on the green/red axis, stop-line detectors, green time so far).
-   **Physics-Based Simulation**: Two lanes per approach carrying a mix of bikes, cars and trucks (different lengths, speeds and acceleration), with car-following, braking, yellow/all-red transitions, minimum green, and random demand whose NS/EW balance shifts over time.
-   **Baselines & Evaluation**: Fixed-cycle, longest-queue and vehicle-actuated controllers, compared on identical traffic (same seeds).
-   **Interactive Dashboard**:
    -   **Live Visualization**: Watch cars move and lights change in real-time.
    -   **Control Panel**: Pause, Resume, Reset, switch the signal controller, and adjust Traffic Density and simulation speed on the fly.
    -   **Real-time Metrics**: Waiting vehicles, measured average wait time, throughput, and queue per approach.
-   **Modern UI**: Built with React, Tailwind CSS, and Recharts for a professional look.

## Results

Average wait per vehicle in simulated seconds (30 unseen episodes per cell, lower is better). Density is demand as a fraction of intersection capacity.

| Controller       | d=0.2 | d=0.4 | d=0.6 | d=0.8 | d=1.0 | Mean |
|------------------|------:|------:|------:|------:|------:|-----:|
| Fixed cycle 20s  |   8.3 |   8.8 |  10.7 |  17.8 |  45.6 | 18.2 |
| Fixed cycle 40s  |  13.4 |  14.2 |  16.2 |  21.9 |  40.5 | 21.2 |
| Longest queue    |   9.3 |   9.9 |  11.7 |  15.0 |  23.5 | 13.9 |
| Vehicle actuated |   3.7 |   7.8 |  14.0 |  20.2 |  35.5 | 16.3 |
| **Q-Learning**   |   3.9 |   5.7 |   7.9 |  10.7 |  19.6 |  **9.5** |

Reproduce with `python backend/evaluate.py --episodes 30`.

## Tech Stack

-   **Backend**: Python, FastAPI, NumPy, Gymnasium (Custom Environment)
-   **Frontend**: React, Vite, Tailwind CSS, Recharts, Lucide React
-   **Communication**: WebSockets for real-time state streaming

## Getting Started

### Prerequisites
-   Python 3.10+
-   Node.js 20.19+

### Installation

1.  **Clone the repository**
    ```bash
    git clone https://github.com/yourusername/traffic-ai.git
    cd traffic-ai
    ```

2.  **Backend Setup**
    ```bash
    # Install Python dependencies
    pip install -r requirements.txt
    ```

3.  **Frontend Setup**
    ```bash
    cd frontend
    npm install
    cd ..
    ```

### Running the Application

1.  **Start the Backend Server**
    ```bash
    uvicorn backend.main:app --reload --port 8000
    ```

2.  **Start the Frontend Client** (in a new terminal)
    ```bash
    cd frontend
    npm run dev
    ```

3.  Open your browser at `http://localhost:5173` to view the simulation (the dev server proxies the WebSocket to port 8000).

Alternatively, build the frontend once (`cd frontend && npm run build`) and open `http://localhost:8000`; the backend serves the built app. Or use Docker:

```bash
docker build -t traffic-ai . && docker run -p 8000:8000 traffic-ai
```

## Training and Evaluating the Agent

```bash
python backend/train.py        # 10000 episodes (~15 min), saves the best table to q_table.npz
python backend/evaluate.py     # compare the agent against the baseline controllers
```

Training samples a random traffic density per episode and periodically scores the greedy policy on fixed evaluation seeds, keeping the best table. `python backend/train.py --help` lists the options.

## Tests

```bash
pip install -r requirements-dev.txt
pytest
```

## Project Structure

```
traffic-ai/
├── backend/
│   ├── traffic_env.py  # Gymnasium traffic environment (physics, signals, demand)
│   ├── agent.py        # State encoder + Q-Learning agent
│   ├── baselines.py    # Fixed-cycle, longest-queue and actuated controllers
│   ├── train.py        # Training script
│   ├── evaluate.py     # Agent vs. baselines benchmark
│   ├── simulation.py   # Live simulation session & WebSocket streaming
│   └── main.py         # FastAPI entry point
├── frontend/
│   ├── src/
│   │   ├── components/ # React components (Canvas, Panels)
│   │   └── App.jsx     # Main frontend logic
│   └── tailwind.config.js
├── tests/              # pytest suite (environment, agent, server)
├── q_table.npz         # Trained model
└── requirements.txt
```

## License

MIT License
