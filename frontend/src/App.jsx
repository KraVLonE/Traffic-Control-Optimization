import React, { useState, useEffect, useRef } from 'react';
import SimulationCanvas from './components/SimulationCanvas';
import MetricsPanel from './components/MetricsPanel';
import ControlPanel from './components/ControlPanel';

function App() {
  const [gameState, setGameState] = useState(null);
  const [connected, setConnected] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const wsRef = useRef(null);

  useEffect(() => {
    // Dynamic WebSocket URL
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    const wsUrl = `${protocol}//${host}/ws/simulation`;

    console.log(`Connecting to WebSocket: ${wsUrl}`);
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log('Connected to simulation server');
      setConnected(true);
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setGameState(data);
    };

    ws.onclose = () => {
      console.log('Disconnected from simulation server');
      setConnected(false);
    };

    return () => {
      ws.close();
    };
  }, []);

  const sendCommand = (type, value = null) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type, value }));
    }
  };

  const handleStart = () => {
    sendCommand('start');
    setIsPaused(false);
  };

  const handleStop = () => {
    sendCommand('stop');
    setIsPaused(true);
  };

  const handleReset = () => {
    sendCommand('reset');
  };

  const handleDensityChange = (value) => {
    sendCommand('set_density', value);
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col items-center p-8 font-sans text-slate-800">
      <div className="max-w-7xl w-full flex flex-col gap-8">

        {/* Header */}
        <div className="flex flex-col items-center text-center space-y-2 mb-4">
          <h1 className="text-3xl font-bold text-slate-900 tracking-tight">
            Traffic Optimization Dashboard
          </h1>
          <p className="text-slate-500 text-sm font-medium">
            Reinforcement Learning Agent • Q-Learning Model
          </p>
        </div>

        {/* Main Content Area */}
        <div className="flex flex-col xl:flex-row gap-8 items-start justify-center">

          {/* Left Column: Simulation */}
          <div className="flex flex-col gap-4">
            <div className="relative shadow-lg rounded-xl overflow-hidden border border-slate-200 bg-white">
              <SimulationCanvas gameState={gameState} />
              {!connected && (
                <div className="absolute inset-0 flex items-center justify-center bg-white/80 backdrop-blur-sm">
                  <div className="flex flex-col items-center gap-4">
                    <div className="w-8 h-8 border-4 border-slate-800 border-t-transparent rounded-full animate-spin"></div>
                    <p className="text-slate-800 font-semibold">Connecting to Server...</p>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Right Column: Controls & Metrics */}
          <div className="flex flex-col gap-6 w-full max-w-md">
            <ControlPanel
              onStart={handleStart}
              onStop={handleStop}
              onReset={handleReset}
              onDensityChange={handleDensityChange}
              isPaused={isPaused}
            />
            <MetricsPanel gameState={gameState} />
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
