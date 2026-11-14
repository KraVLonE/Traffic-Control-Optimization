import React from 'react';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
import { Clock, Activity, Car, Zap, Gauge, Flag } from 'lucide-react';

const LANES = ['N', 'S', 'E', 'W'];

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

    const { north_south: ns, east_west: ew } = gameState.lights;
    const phase = ns === 'green' ? { label: 'North-South Flow', text: 'text-emerald-600', dot: 'bg-emerald-500' }
        : ew === 'green' ? { label: 'East-West Flow', text: 'text-blue-600', dot: 'bg-blue-500' }
        : { label: 'Changing…', text: 'text-amber-600', dot: 'bg-amber-500' };

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
                        <span className="text-xs font-semibold uppercase tracking-wider">Waiting Now</span>
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

                <div className="bg-slate-50 p-4 rounded-lg border border-slate-100">
                    <div className="flex items-center gap-2 mb-2 text-slate-500">
                        <Gauge size={16} />
                        <span className="text-xs font-semibold uppercase tracking-wider">Throughput</span>
                    </div>
                    <p className="text-3xl font-bold text-slate-800">
                        {gameState.metrics.throughput}<span className="text-sm font-medium text-slate-400"> /min</span>
                    </p>
                </div>

                <div className="bg-slate-50 p-4 rounded-lg border border-slate-100">
                    <div className="flex items-center gap-2 mb-2 text-slate-500">
                        <Flag size={16} />
                        <span className="text-xs font-semibold uppercase tracking-wider">Vehicles Served</span>
                    </div>
                    <p className="text-3xl font-bold text-slate-800">{gameState.metrics.completed}</p>
                </div>

                <div className="bg-slate-50 p-4 rounded-lg border border-slate-100 col-span-2">
                    <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">Queue per Approach</span>
                    <div className="grid grid-cols-4 gap-2 mt-2">
                        {LANES.map((name, i) => (
                            <div key={name} className="text-center">
                                <p className="text-xl font-bold text-slate-800">{gameState.metrics.lane_queues[i]}</p>
                                <p className="text-xs text-slate-400">{name}</p>
                            </div>
                        ))}
                    </div>
                </div>

                <div className="bg-slate-50 p-4 rounded-lg border border-slate-100 col-span-2 flex items-center justify-between">
                    <div>
                        <div className="flex items-center gap-2 mb-1 text-slate-500">
                            <Zap size={16} />
                            <span className="text-xs font-semibold uppercase tracking-wider">Active Phase</span>
                        </div>
                        <p className={`text-lg font-bold ${phase.text}`}>{phase.label}</p>
                    </div>
                    <div className={`w-3 h-3 rounded-full ${phase.dot}`} />
                </div>
            </div>

            {/* Performance Graph */}
            <div className="h-48 w-full bg-white rounded-lg p-2 border border-slate-100">
                <p className="text-xs text-slate-400 mb-2 ml-2">Waiting Vehicles (last 5 simulated minutes)</p>
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
