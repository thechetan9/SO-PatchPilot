'use client';

import { useState } from 'react';
import DashboardHeader from '@/components/DashboardHeader';
import PlansView from '@/components/PlansView';
import RunsView from '@/components/RunsView';
import KPIView from '@/components/KPIView';

type TabType = 'plans' | 'runs' | 'kpis';

export default function Home() {
  const [activeTab, setActiveTab] = useState<TabType>('plans');

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      <DashboardHeader />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Tab Navigation */}
        <div className="flex gap-4 mb-8 border-b border-slate-700">
          <button
            onClick={() => setActiveTab('plans')}
            className={`px-4 py-2 font-medium transition-colors ${
              activeTab === 'plans'
                ? 'text-blue-400 border-b-2 border-blue-400'
                : 'text-slate-400 hover:text-slate-300'
            }`}
          >
            📋 Open Plans
          </button>
          <button
            onClick={() => setActiveTab('runs')}
            className={`px-4 py-2 font-medium transition-colors ${
              activeTab === 'runs'
                ? 'text-blue-400 border-b-2 border-blue-400'
                : 'text-slate-400 hover:text-slate-300'
            }`}
          >
            🚀 Patch Runs
          </button>
          <button
            onClick={() => setActiveTab('kpis')}
            className={`px-4 py-2 font-medium transition-colors ${
              activeTab === 'kpis'
                ? 'text-blue-400 border-b-2 border-blue-400'
                : 'text-slate-400 hover:text-slate-300'
            }`}
          >
            📊 KPIs & Analytics
          </button>
        </div>

        {/* Tab Content */}
        <div>
          {activeTab === 'plans' && <PlansView />}
          {activeTab === 'runs' && <RunsView />}
          {activeTab === 'kpis' && <KPIView />}
        </div>
      </main>
    </div>
  );
}
