import os
import sys
from pathlib import Path

from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles

# Allow `uvicorn backend.main:app` from the project root as well as running from backend/.
BACKEND_DIR = Path(__file__).resolve().parent
ROOT_DIR = BACKEND_DIR.parent
sys.path.append(str(BACKEND_DIR))

from agent import QLearningAgent  # noqa: E402
from simulation import Simulation  # noqa: E402

MODEL_PATH = Path(os.environ.get("TRAFFIC_MODEL", ROOT_DIR / "q_table.npz"))
STATIC_DIR = ROOT_DIR / "frontend" / "dist"


def load_agent():
    agent = QLearningAgent()
    try:
        agent.load(MODEL_PATH)
    except (FileNotFoundError, ValueError) as exc:
        print(f"Warning: no usable model at {MODEL_PATH} ({exc}). "
              "Run `python backend/train.py`; serving baseline controllers only.")
        return None
    print(f"Loaded trained model from {MODEL_PATH}.")
    return agent


app = FastAPI(title="Traffic AI")
agent = load_agent()  # read-only at serve time, shared by all sessions


@app.get("/api/health")
def health():
    return {"status": "ok", "model_loaded": agent is not None}


@app.websocket("/ws/simulation")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    await Simulation(agent).run(websocket)


# Serve the built React app (production). Mounted last so it doesn't shadow the API.
if STATIC_DIR.exists():
    app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
else:
    print("Warning: frontend/dist not found. Static files will not be served.")
