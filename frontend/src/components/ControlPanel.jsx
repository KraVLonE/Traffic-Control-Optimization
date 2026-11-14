import React from 'react';
import { Play, Pause, RotateCcw, Settings } from 'lucide-react';

const CONTROLLER_LABELS = {
    q_learning: 'Q-Learning Agent',
    fixed_20: 'Fixed Cycle (20s)',
    fixed_40: 'Fixed Cycle (40s)',
    longest_queue: 'Longest Queue First',
    actuated: 'Vehicle Actuated',
};

const SPEEDS = [0.5, 1, 2, 4];

const ControlPanel = ({
    onStart, onStop, onReset, onDensityChange, onControllerChange, onSpeedChange,
    controllers, controller, density, speed, isPaused,
}) => {
    return (
        <div className="bg-white p-6 rounded-lg shadow-sm border border-slate-200 w-full max-w-md flex flex-col gap-6">
            <div className="flex items-center gap-2 border-b border-slate-100 pb-4">
                <Settings className="text-slate-500" size={20} />
                <h2 className="text-lg font-semibold text-slate-800">Simulation Controls</h2>
            </div>

            {/* Action Buttons */}
            <div className="flex gap-4">
                {!isPaused ? (
                    <button
                        onClick={onStop}
                        className="flex-1 flex items-center justify-center gap-2 bg-amber-500 hover:bg-amber-600 text-white py-2 px-4 rounded-md font-medium transition-colors"
                    >
                        <Pause size={18} /> Pause
                    </button>
                ) : (
                    <button
                        onClick={onStart}
                        className="flex-1 flex items-center justify-center gap-2 bg-emerald-600 hover:bg-emerald-700 text-white py-2 px-4 rounded-md font-medium transition-colors"
                    >
                        <Play size={18} /> Resume
                    </button>
                )}

                <button
                    onClick={onReset}
                    className="flex-1 flex items-center justify-center gap-2 bg-slate-100 hover:bg-slate-200 text-slate-700 py-2 px-4 rounded-md font-medium transition-colors border border-slate-300"
                >
                    <RotateCcw size={18} /> Reset
                </button>
            </div>

            {/* Controller */}
            <div className="space-y-2">
                <label htmlFor="controller" className="block text-sm font-medium text-slate-600">
                    Signal Controller
                </label>
                <select
                    id="controller"
                    value={controller}
                    onChange={(e) => onControllerChange(e.target.value)}
                    className="w-full border border-slate-300 rounded-md py-2 px-3 text-sm text-slate-700 bg-white"
                >
                    {controllers.map((name) => (
                        <option key={name} value={name}>{CONTROLLER_LABELS[name] ?? name}</option>
                    ))}
                </select>
            </div>

            {/* Density Slider */}
            <div className="space-y-2">
                <div className="flex justify-between text-sm text-slate-600">
                    <span className="font-medium">Traffic Density</span>
                    <span>{Math.round(density * 100)}% of capacity</span>
                </div>
                <input
                    type="range"
                    min="0.1"
                    max="1.2"
                    step="0.05"
                    value={density}
                    onChange={(e) => onDensityChange(parseFloat(e.target.value))}
                    className="w-full h-2 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
                />
                <div className="flex justify-between text-xs text-slate-400">
                    <span>Light</span>
                    <span>Oversaturated</span>
                </div>
            </div>

            {/* Simulation Speed */}
            <div className="space-y-2">
                <span className="block text-sm font-medium text-slate-600">Simulation Speed</span>
                <div className="flex gap-2">
                    {SPEEDS.map((s) => (
                        <button
                            key={s}
                            onClick={() => onSpeedChange(s)}
                            className={`flex-1 py-1.5 rounded-md text-sm font-medium border transition-colors ${
                                speed === s
                                    ? 'bg-slate-800 text-white border-slate-800'
                                    : 'bg-white text-slate-600 border-slate-300 hover:bg-slate-100'
                            }`}
                        >
                            {s}x
                        </button>
                    ))}
                </div>
            </div>
        </div>
    );
};

export default ControlPanel;
