import json

from fastapi.testclient import TestClient

import main
from simulation import Simulation


def test_simulation_advances_and_handles_commands():
    sim = Simulation(agent=None)
    sim.handle_command({"type": "set_density", "value": 0.9})
    sim.handle_command({"type": "set_controller", "value": "longest_queue"})
    sim.handle_command({"type": "set_controller", "value": "does_not_exist"})
    for _ in range(300):
        sim.advance()
    snap = sim.snapshot()
    assert snap["controller"] == "longest_queue"
    assert snap["density"] == 0.9
    assert snap["metrics"]["step"] == 300
    assert snap["metrics"]["completed"] > 0
    assert set(snap["lights"].values()) <= {"green", "yellow", "red"}
    json.dumps(snap)  # must be serialisable


def test_websocket_stream_and_isolated_sessions():
    client = TestClient(main.app)
    assert client.get("/api/health").json()["status"] == "ok"
    with client.websocket_connect("/ws/simulation") as a, client.websocket_connect("/ws/simulation") as b:
        a.send_text(json.dumps({"type": "stop"}))
        a.send_text("not json")  # ignored, must not kill the session
        paused = False
        for _ in range(20):
            paused = a.receive_json()["paused"]
            if paused:
                break
        assert paused
        assert b.receive_json()["paused"] is False  # other client is unaffected
