from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
import sys
import os

# Add current directory to sys.path to allow imports from backend folder
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from simulation import Simulation

from fastapi.staticfiles import StaticFiles

# ... existing imports ...

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

simulation = Simulation(model_path="q_table.pkl")

@app.websocket("/ws/simulation")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("Client connected")
    try:
        await simulation.run_loop(websocket)
    except Exception as e:
        print(f"Connection closed: {e}")
    finally:
        print("Client disconnected")

# Serve React Static Files (Production)
# Mount this LAST so it doesn't override API routes
if os.path.exists("../frontend/dist"):
    app.mount("/", StaticFiles(directory="../frontend/dist", html=True), name="static")
elif os.path.exists("frontend/dist"):
    app.mount("/", StaticFiles(directory="frontend/dist", html=True), name="static")
else:
    print("Warning: frontend/dist not found. Static files will not be served.")
