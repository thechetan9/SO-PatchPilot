'use client';

export default function DashboardHeader() {
  return (
    <header className="bg-slate-950 border-b border-slate-700 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="text-3xl">🔧</div>
            <div>
              <h1 className="text-2xl font-bold text-white">PatchPilot</h1>
              <p className="text-sm text-slate-400">AI-Powered Patch Management</p>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <div className="text-right">
              <p className="text-sm text-slate-400">Status</p>
              <p className="text-lg font-semibold text-green-400">🟢 Live</p>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}

