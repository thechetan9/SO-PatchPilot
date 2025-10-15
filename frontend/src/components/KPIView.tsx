'use client';

import { useState, useEffect } from 'react';

interface KPIData {
  period_days: number;
  summary: {
    total_patches: number;
    successful_patches: number;
    failed_patches: number;
    average_success_rate: number;
    average_duration_hours: number;
    total_exposure_hours_reduced: number;
    total_rollbacks: number;
    manual_touches_reduced_percent: number;
  };
  trends: {
    success_rate_trend: number[];
    duration_trend: number[];
    exposure_hours_trend: number[];
  };
  generated_at: string;
}

export default function KPIView() {
  const [kpis, setKpis] = useState<KPIData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchKPIs();
  }, []);

  const fetchKPIs = async () => {
    try {
      setLoading(true);
      const response = await fetch('http://localhost:5000/api/dashboard/kpis');
      if (!response.ok) throw new Error('Failed to fetch KPIs');
      const data = await response.json();
      setKpis(data);
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

  if (error || !kpis) {
    return (
      <div className="bg-red-900/20 border border-red-700 rounded-lg p-4 text-red-200">
        Error: {error || 'Failed to load KPIs'}
      </div>
    );
  }

  const { summary, trends } = kpis;

  return (
    <div className="space-y-8">
      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-slate-800 border border-slate-700 rounded-lg p-6">
          <p className="text-sm text-slate-400 mb-2">Total Patches</p>
          <p className="text-3xl font-bold text-blue-400">{summary.total_patches}</p>
          <p className="text-xs text-green-400 mt-2">✓ {summary.successful_patches} successful</p>
        </div>

        <div className="bg-slate-800 border border-slate-700 rounded-lg p-6">
          <p className="text-sm text-slate-400 mb-2">Success Rate</p>
          <p className="text-3xl font-bold text-green-400">{summary.average_success_rate}%</p>
          <p className="text-xs text-red-400 mt-2">✗ {summary.failed_patches} failed</p>
        </div>

        <div className="bg-slate-800 border border-slate-700 rounded-lg p-6">
          <p className="text-sm text-slate-400 mb-2">Avg Duration</p>
          <p className="text-3xl font-bold text-purple-400">{summary.average_duration_hours}h</p>
          <p className="text-xs text-slate-400 mt-2">per patch run</p>
        </div>

        <div className="bg-slate-800 border border-slate-700 rounded-lg p-6">
          <p className="text-sm text-slate-400 mb-2">Exposure Reduced</p>
          <p className="text-3xl font-bold text-orange-400">{summary.total_exposure_hours_reduced}</p>
          <p className="text-xs text-slate-400 mt-2">device-hours</p>
        </div>
      </div>

      {/* Additional Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="bg-slate-800 border border-slate-700 rounded-lg p-6">
          <p className="text-sm text-slate-400 mb-4">Rollbacks</p>
          <p className="text-4xl font-bold text-red-400">{summary.total_rollbacks}</p>
          <p className="text-xs text-slate-400 mt-2">automatic rollbacks triggered</p>
        </div>

        <div className="bg-slate-800 border border-slate-700 rounded-lg p-6">
          <p className="text-sm text-slate-400 mb-4">Manual Touches Reduced</p>
          <p className="text-4xl font-bold text-green-400">{summary.manual_touches_reduced_percent}%</p>
          <p className="text-xs text-slate-400 mt-2">automation improvement</p>
        </div>
      </div>

      {/* Trends */}
      <div className="bg-slate-800 border border-slate-700 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-white mb-6">📈 Trends (Last 30 Days)</h3>
        
        <div className="space-y-6">
          {/* Success Rate Trend */}
          <div>
            <p className="text-sm text-slate-400 mb-3">Success Rate Trend</p>
            <div className="flex items-end gap-2 h-24">
              {trends.success_rate_trend.map((value, idx) => (
                <div
                  key={idx}
                  className="flex-1 bg-green-500 rounded-t transition-all hover:bg-green-400"
                  style={{ height: `${(value / 100) * 100}%` }}
                  title={`${value}%`}
                ></div>
              ))}
            </div>
          </div>

          {/* Duration Trend */}
          <div>
            <p className="text-sm text-slate-400 mb-3">Duration Trend (hours)</p>
            <div className="flex items-end gap-2 h-24">
              {trends.duration_trend.map((value, idx) => (
                <div
                  key={idx}
                  className="flex-1 bg-purple-500 rounded-t transition-all hover:bg-purple-400"
                  style={{ height: `${(value / Math.max(...trends.duration_trend)) * 100}%` }}
                  title={`${value}h`}
                ></div>
              ))}
            </div>
          </div>

          {/* Exposure Hours Trend */}
          <div>
            <p className="text-sm text-slate-400 mb-3">Exposure Hours Reduced Trend</p>
            <div className="flex items-end gap-2 h-24">
              {trends.exposure_hours_trend.map((value, idx) => (
                <div
                  key={idx}
                  className="flex-1 bg-orange-500 rounded-t transition-all hover:bg-orange-400"
                  style={{ height: `${(value / Math.max(...trends.exposure_hours_trend)) * 100}%` }}
                  title={`${value}h`}
                ></div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

