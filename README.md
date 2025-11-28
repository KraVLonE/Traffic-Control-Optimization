# Traffic AI Optimization Agent

![Traffic Control Optimization](https://via.placeholder.com/800x400?text=Traffic+AI+Simulation+Dashboard)

A Reinforcement Learning (Q-Learning) project that optimizes traffic flow at a 4-way intersection. The agent learns to control traffic lights to minimize total queue length and average wait times.

## Features

-   **Reinforcement Learning Agent**: Uses Q-Learning to make real-time decisions based on traffic density.
-   **Physics-Based Simulation**: Realistic traffic flow with individual vehicle tracking, acceleration, and braking logic.
-   **Interactive Dashboard**:
    -   **Live Visualization**: Watch cars move and lights change in real-time.
    -   **Control Panel**: Pause, Resume, Reset, and adjust Traffic Density on the fly.
    -   **Real-time Metrics**: Monitor Total Queue, Avg Wait Time, and Performance History.
-   **Modern UI**: Built with React, Tailwind CSS, and Recharts for a professional look.

## Tech Stack

-   **Backend**: Python, FastAPI, NumPy, Gymnasium (Custom Environment)
-   **Frontend**: React, Vite, Tailwind CSS, Recharts, Lucide React
-   **Communication**: WebSockets for real-time state streaming

## Getting Started

### Prerequisites
-   Python 3.8+
-   Node.js 16+

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

3.  Open your browser at `http://localhost:5173` to view the simulation.

## Training the Agent

To retrain the Q-Learning agent from scratch:

```bash
python3 backend/train.py
```
This will run 1000 episodes and save the new model to `q_table.pkl`.

## Project Structure

```
traffic-ai/
├── backend/
│   ├── agent.py        # Q-Learning Agent implementation
│   ├── mock_env.py     # Custom Gymnasium Traffic Environment
│   ├── simulation.py   # Simulation loop & WebSocket logic
│   ├── train.py        # Training script
│   └── main.py         # FastAPI entry point
├── frontend/
│   ├── src/
│   │   ├── components/ # React components (Canvas, Panels)
│   │   └── App.jsx     # Main frontend logic
│   └── tailwind.config.js
└── requirements.txt
```

## License

MIT License
