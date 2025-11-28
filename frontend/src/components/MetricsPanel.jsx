import React from 'react';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
import { Clock, Activity, Car, Zap } from 'lucide-react';

const MetricsPanel = ({ gameState }) => {
    if (!gameState) return (
        <div className="bg-white p-6 rounded-lg shadow-sm border border-slate-200 w-full max-w-md h-[400px] flex items-center justify-center">
            <p className="text-slate-400">Waiting for simulation data...</p>
        </div>
    );

    // Prepare data for chart
    const chartData = gameState.metrics.history.map((val, idx) => ({
        step: idx,
        queue: val
    }));

    return (
        <div className="bg-white p-6 rounded-lg shadow-sm border border-slate-200 w-full max-w-md flex flex-col gap-6">
            <div className="flex items-center justify-between border-b border-slate-100 pb-4">
                <h2 className="text-lg font-semibold text-slate-800">
                    Live Analytics
                </h2>
                <Activity className="text-slate-400" size={20} />
            </div>

            {/* Key Metrics Grid */}
            <div className="grid grid-cols-2 gap-4">
                <div className="bg-slate-50 p-4 rounded-lg border border-slate-100">
                    <div className="flex items-center gap-2 mb-2 text-slate-500">
                        <Car size={16} />
                        <span className="text-xs font-semibold uppercase tracking-wider">Total Queue</span>
                    </div>
                    <p className="text-3xl font-bold text-slate-800">{gameState.metrics.total_queue}</p>
                </div>

                <div className="bg-slate-50 p-4 rounded-lg border border-slate-100">
                    <div className="flex items-center gap-2 mb-2 text-slate-500">
                        <Clock size={16} />
                        <span className="text-xs font-semibold uppercase tracking-wider">Avg Wait Time</span>
                    </div>
                    <p className="text-3xl font-bold text-emerald-600">{gameState.metrics.avg_wait_time}s</p>
                </div>

                <div className="bg-slate-50 p-4 rounded-lg border border-slate-100 col-span-2 flex items-center justify-between">
                    <div>
                        <div className="flex items-center gap-2 mb-1 text-slate-500">
                            <Zap size={16} />
                            <span className="text-xs font-semibold uppercase tracking-wider">Active Phase</span>
                        </div>
                        <p className={`text-lg font-bold ${gameState.lights.north_south === 'green' ? 'text-emerald-600' : 'text-blue-600'}`}>
                            {gameState.lights.north_south === 'green' ? 'North-South Flow' : 'East-West Flow'}
                        </p>
                    </div>
                    <div className={`w-3 h-3 rounded-full ${gameState.lights.north_south === 'green' ? 'bg-emerald-500' : 'bg-blue-500'}`} />
                </div>
            </div>

            {/* Performance Graph */}
            <div className="h-48 w-full bg-white rounded-lg p-2 border border-slate-100">
                <p className="text-xs text-slate-400 mb-2 ml-2">Queue History (Last 20 Steps)</p>
                <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={chartData}>
                        <Line
                            type="monotone"
                            dataKey="queue"
                            stroke="#64748b"
                            strokeWidth={2}
                            dot={false}
                            isAnimationActive={false}
                        />
                        <YAxis hide domain={[0, 'auto']} />
                        <Tooltip
                            contentStyle={{ backgroundColor: '#fff', border: '1px solid #e2e8f0', borderRadius: '8px', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                            itemStyle={{ color: '#1e293b' }}
                        />
                    </LineChart>
                </ResponsiveContainer>
            </div>
        </div>
    );
};

export default MetricsPanel;
