'use client';

import { useState, useEffect } from 'react';

interface BatchProgress {
  devices: number;
  status: string;
  successful: number;
}

interface Run {
  run_id: string;
  plan_id: string;
  status: string;
  current_batch?: string;
  progress?: {
    canary: BatchProgress;
    batch_1: BatchProgress;
    batch_2: BatchProgress;
  };
  started_at: string;
  estimated_completion?: string;
  devices_patched?: number;
  success_rate?: number;
  duration_hours?: number;
  completed_at?: string;
}

export default function RunsView() {
  const [inProgress, setInProgress] = useState<Run[]>([]);
  const [recent, setRecent] = useState<Run[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchRuns();
  }, []);

  const fetchRuns = async () => {
    try {
      setLoading(true);
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'https://byeh9xee0k.execute-api.us-east-1.amazonaws.com/dev';
      const response = await fetch(`${apiUrl}/api/dashboard/runs`);
      if (!response.ok) throw new Error('Failed to fetch runs');
      const data = await response.json();
      setInProgress(data.in_progress || []);
      setRecent(data.recent || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-400"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-red-400">Error: {error}</div>
      </div>
    );
  }

  const renderBatchStatus = (batch: BatchProgress) => {
    const percentage = (batch.successful / batch.devices) * 100;
    return (
      <div className="mb-3">
        <div className="flex justify-between text-sm mb-1">
          <span className="text-slate-300">{batch.devices} devices</span>
          <span className="text-blue-400">{percentage.toFixed(0)}%</span>
        </div>
        <div className="w-full bg-slate-700 rounded-full h-2">
          <div
            className="bg-blue-500 h-2 rounded-full transition-all"
            style={{ width: `${percentage}%` }}
          ></div>
        </div>
      </div>
    );
  };

  return (
    <div className="space-y-8">
      {/* In Progress */}
      {inProgress.length > 0 && (
        <div>
          <h2 className="text-xl font-bold text-white mb-4">🚀 In Progress</h2>
          <div className="space-y-4">
            {inProgress.map((run) => (
              <div
                key={run.run_id}
                className="bg-slate-800 border border-slate-700 rounded-lg p-6"
              >
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <h3 className="text-lg font-semibold text-white">{run.run_id}</h3>
                    <p className="text-sm text-slate-400">Plan: {run.plan_id}</p>
                  </div>
                  <span className="px-3 py-1 bg-blue-900/30 text-blue-300 rounded-full text-sm font-medium">
                    Executing
                  </span>
                </div>

                {run.progress && (
                  <div className="grid grid-cols-3 gap-4 mb-4">
                    <div className="bg-slate-900 rounded p-3">
                      <p className="text-xs text-slate-400 mb-2">Canary</p>
                      {renderBatchStatus(run.progress.canary)}
                    </div>
                    <div className="bg-slate-900 rounded p-3">
                      <p className="text-xs text-slate-400 mb-2">Batch 1</p>
                      {renderBatchStatus(run.progress.batch_1)}
                    </div>
                    <div className="bg-slate-900 rounded p-3">
                      <p className="text-xs text-slate-400 mb-2">Batch 2</p>
                      {renderBatchStatus(run.progress.batch_2)}
                    </div>
                  </div>
                )}

                <p className="text-sm text-slate-400">
                  Started: {new Date(run.started_at).toLocaleString()}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Recent Completed */}
      {recent.length > 0 && (
        <div>
          <h2 className="text-xl font-bold text-white mb-4">✓ Recently Completed</h2>
          <div className="space-y-4">
            {recent.map((run) => (
              <div
                key={run.run_id}
                className="bg-slate-800 border border-slate-700 rounded-lg p-6"
              >
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <h3 className="text-lg font-semibold text-white">{run.run_id}</h3>
                    <p className="text-sm text-slate-400">Plan: {run.plan_id}</p>
                  </div>
                  <span className="px-3 py-1 bg-green-900/30 text-green-300 rounded-full text-sm font-medium">
                    Completed
                  </span>
                </div>

                <div className="grid grid-cols-4 gap-4">
                  <div>
                    <p className="text-sm text-slate-400">Devices Patched</p>
                    <p className="text-2xl font-bold text-blue-400">{run.devices_patched}</p>
                  </div>
                  <div>
                    <p className="text-sm text-slate-400">Success Rate</p>
                    <p className="text-2xl font-bold text-green-400">{run.success_rate}%</p>
                  </div>
                  <div>
                    <p className="text-sm text-slate-400">Duration</p>
                    <p className="text-2xl font-bold text-slate-200">{run.duration_hours}h</p>
                  </div>
                  <div>
                    <p className="text-sm text-slate-400">Completed</p>
                    <p className="text-sm text-slate-200">
                      {new Date(run.completed_at || '').toLocaleDateString()}
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {inProgress.length === 0 && recent.length === 0 && (
        <div className="text-center py-12 text-slate-400">
          <p className="text-lg">No patch runs</p>
        </div>
      )}
    </div>
  );
}

