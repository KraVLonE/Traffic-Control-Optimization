import React from 'react';
import { Play, Pause, RotateCcw, Settings } from 'lucide-react';

const ControlPanel = ({ onStart, onStop, onReset, onDensityChange, isPaused }) => {
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

            {/* Density Slider */}
            <div className="space-y-2">
                <div className="flex justify-between text-sm text-slate-600">
                    <span className="font-medium">Traffic Density</span>
                    <span>Adjust Arrival Rate</span>
                </div>
                <input
                    type="range"
                    min="0.1"
                    max="0.8"
                    step="0.1"
                    defaultValue="0.3"
                    onChange={(e) => onDensityChange(parseFloat(e.target.value))}
                    className="w-full h-2 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
                />
                <div className="flex justify-between text-xs text-slate-400">
                    <span>Low</span>
                    <span>High</span>
                </div>
            </div>
        </div>
    );
};

export default ControlPanel;
