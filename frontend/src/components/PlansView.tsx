'use client';

import { useState, useEffect } from 'react';

interface Plan {
  plan_id: string;
  client_id: string;
  ticket_id?: string;
  status: string;
  created_at: string;
  devices_affected?: string[];
  patches?: number;
  strategy?: string;
  canary_size: number;
  batches: number[];
  estimated_duration_hours: number;
  device_count?: number;
  health_check_interval_minutes?: number;
  rollback_threshold_percent?: number;
  notes?: string;
  approved_at?: string;
  rejected_at?: string;
}

export default function PlansView() {
  const [plans, setPlans] = useState<Plan[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedPlan, setSelectedPlan] = useState<Plan | null>(null);
  const [showHistory, setShowHistory] = useState(false);
  const [history, setHistory] = useState<Plan[]>([]);
  const [generating, setGenerating] = useState(false);
  const [editMode, setEditMode] = useState(false);
  const [editedPlan, setEditedPlan] = useState<Plan | null>(null);

  useEffect(() => {
    fetchPlans();
  }, []);

  const fetchPlans = async () => {
    try {
      setLoading(true);
      const response = await fetch('http://localhost:5000/api/dashboard/plans');
      if (!response.ok) throw new Error('Failed to fetch plans');
      const data = await response.json();
      setPlans(data.open_plans || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async (planId: string) => {
    try {
      const response = await fetch('http://localhost:5000/api/dashboard/approve-plan', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ plan_id: planId, approved_by: 'user@company.com' }),
      });
      if (!response.ok) throw new Error('Failed to approve plan');
      alert(`✓ Plan ${planId} approved!`);
      fetchPlans();
    } catch (err) {
      alert(`Error: ${err instanceof Error ? err.message : 'Unknown error'}`);
    }
  };

  const handleReject = async (planId: string) => {
    try {
      const response = await fetch('http://localhost:5000/api/dashboard/reject-plan', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ plan_id: planId, rejected_by: 'user@company.com', reason: 'Needs review' }),
      });
      if (!response.ok) throw new Error('Failed to reject plan');
      alert(`✗ Plan ${planId} rejected!`);
      fetchPlans();
    } catch (err) {
      alert(`Error: ${err instanceof Error ? err.message : 'Unknown error'}`);
    }
  };

  const generateNewPlan = async () => {
    setGenerating(true);
    try {
      const response = await fetch('http://localhost:5000/api/dashboard/plans/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          client_id: 'client-a',
          canary_size: 5,
          batches: [30, 30],
          estimated_duration_hours: 6,
          device_count: 65,
          patches: 0,
        }),
      });
      if (!response.ok) throw new Error('Failed to generate plan');
      alert('✓ New plan generated!');
      fetchPlans();
    } catch (err) {
      alert(`Error: ${err instanceof Error ? err.message : 'Unknown error'}`);
    } finally {
      setGenerating(false);
    }
  };

  const fetchHistory = async () => {
    try {
      const response = await fetch('http://localhost:5000/api/dashboard/plans/history');
      if (!response.ok) throw new Error('Failed to fetch history');
      const data = await response.json();
      setHistory(data.all_plans || []);
      setShowHistory(true);
    } catch (err) {
      alert(`Error: ${err instanceof Error ? err.message : 'Unknown error'}`);
    }
  };

  const startEdit = () => {
    if (selectedPlan) {
      setEditedPlan({ ...selectedPlan });
      setEditMode(true);
    }
  };

  const saveEdit = async () => {
    if (!editedPlan) return;
    try {
      // Update the plan in the backend
      const response = await fetch('http://localhost:5000/api/dashboard/plans/update', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(editedPlan),
      });
      if (!response.ok) throw new Error('Failed to update plan');
      alert('✓ Plan updated!');
      setEditMode(false);
      setSelectedPlan(editedPlan);
      fetchPlans();
    } catch (err) {
      alert(`Error: ${err instanceof Error ? err.message : 'Unknown error'}`);
    }
  };

  const exportPlan = () => {
    if (!selectedPlan) return;
    const dataStr = JSON.stringify(selectedPlan, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `${selectedPlan.plan_id}.json`;
    link.click();
    URL.revokeObjectURL(url);
  };

  const duplicatePlan = async () => {
    if (!selectedPlan) return;
    setGenerating(true);
    try {
      const response = await fetch('http://localhost:5000/api/dashboard/plans/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          client_id: selectedPlan.client_id,
          canary_size: selectedPlan.canary_size,
          batches: selectedPlan.batches,
          estimated_duration_hours: selectedPlan.estimated_duration_hours,
          device_count: selectedPlan.device_count,
          patches: selectedPlan.patches,
        }),
      });
      if (!response.ok) throw new Error('Failed to duplicate plan');
      alert('✓ Plan duplicated!');
      setSelectedPlan(null);
      fetchPlans();
    } catch (err) {
      alert(`Error: ${err instanceof Error ? err.message : 'Unknown error'}`);
    } finally {
      setGenerating(false);
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
      <div className="bg-red-900/20 border border-red-700 rounded-lg p-4 text-red-200">
        Error: {error}
      </div>
    );
  }

  // Show plan details if selected
  if (selectedPlan) {
    const displayPlan = editMode && editedPlan ? editedPlan : selectedPlan;

    return (
      <div className="space-y-6">
        <button
          onClick={() => {
            setSelectedPlan(null);
            setEditMode(false);
          }}
          className="text-blue-400 hover:text-blue-300 mb-4 flex items-center gap-2"
        >
          ← Back to Plans
        </button>

        <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
          <div className="flex justify-between items-start mb-6">
            <div>
              <h2 className="text-2xl font-bold text-white">{displayPlan.plan_id}</h2>
              <p className="text-gray-400">Client: {displayPlan.client_id}</p>
            </div>
            <span className={`px-3 py-1 rounded text-sm font-medium ${
              displayPlan.status === 'pending_approval' ? 'bg-yellow-900 text-yellow-200' :
              displayPlan.status === 'approved' ? 'bg-green-900 text-green-200' :
              'bg-red-900 text-red-200'
            }`}>
              {displayPlan.status}
            </span>
          </div>

          <div className="grid grid-cols-2 gap-4 mb-6">
            <div className="bg-slate-700 p-4 rounded">
              <p className="text-gray-400 text-sm">Strategy</p>
              {editMode && editedPlan ? (
                <input
                  type="text"
                  value={editedPlan.strategy || 'canary_then_batch'}
                  onChange={(e) => setEditedPlan({ ...editedPlan, strategy: e.target.value })}
                  className="w-full bg-slate-600 text-white rounded px-2 py-1 mt-1"
                />
              ) : (
                <p className="text-white font-semibold">{displayPlan.strategy || 'canary_then_batch'}</p>
              )}
            </div>
            <div className="bg-slate-700 p-4 rounded">
              <p className="text-gray-400 text-sm">Duration (hours)</p>
              {editMode && editedPlan ? (
                <input
                  type="number"
                  value={editedPlan.estimated_duration_hours}
                  onChange={(e) => setEditedPlan({ ...editedPlan, estimated_duration_hours: parseInt(e.target.value) })}
                  className="w-full bg-slate-600 text-white rounded px-2 py-1 mt-1"
                />
              ) : (
                <p className="text-white font-semibold">{displayPlan.estimated_duration_hours}h</p>
              )}
            </div>
            <div className="bg-slate-700 p-4 rounded">
              <p className="text-gray-400 text-sm">Total Devices</p>
              {editMode && editedPlan ? (
                <input
                  type="number"
                  value={editedPlan.device_count || 0}
                  onChange={(e) => setEditedPlan({ ...editedPlan, device_count: parseInt(e.target.value) })}
                  className="w-full bg-slate-600 text-white rounded px-2 py-1 mt-1"
                />
              ) : (
                <p className="text-white font-semibold">{displayPlan.device_count || 'N/A'}</p>
              )}
            </div>
            <div className="bg-slate-700 p-4 rounded">
              <p className="text-gray-400 text-sm">Patches</p>
              {editMode && editedPlan ? (
                <input
                  type="number"
                  value={editedPlan.patches || 0}
                  onChange={(e) => setEditedPlan({ ...editedPlan, patches: parseInt(e.target.value) })}
                  className="w-full bg-slate-600 text-white rounded px-2 py-1 mt-1"
                />
              ) : (
                <p className="text-white font-semibold">{displayPlan.patches || 'N/A'}</p>
              )}
            </div>
          </div>

          <div className="mb-6">
            <h3 className="text-lg font-semibold text-white mb-4">Deployment Phases</h3>
            <div className="space-y-3">
              <div className="bg-slate-700 p-4 rounded">
                <p className="text-gray-400 text-sm">Canary Batch</p>
                {editMode && editedPlan ? (
                  <input
                    type="number"
                    value={editedPlan.canary_size}
                    onChange={(e) => setEditedPlan({ ...editedPlan, canary_size: parseInt(e.target.value) })}
                    className="w-full bg-slate-600 text-white rounded px-2 py-1 mt-1"
                  />
                ) : (
                  <p className="text-white font-semibold">{displayPlan.canary_size} devices</p>
                )}
                <p className="text-gray-500 text-xs mt-1">Test patch on small subset first</p>
              </div>
              {displayPlan.batches.map((size, idx) => (
                <div key={idx} className="bg-slate-700 p-4 rounded">
                  <p className="text-gray-400 text-sm">Batch {idx + 1}</p>
                  {editMode && editedPlan ? (
                    <input
                      type="number"
                      value={editedPlan.batches[idx]}
                      onChange={(e) => {
                        const newBatches = [...editedPlan.batches];
                        newBatches[idx] = parseInt(e.target.value);
                        setEditedPlan({ ...editedPlan, batches: newBatches });
                      }}
                      className="w-full bg-slate-600 text-white rounded px-2 py-1 mt-1"
                    />
                  ) : (
                    <p className="text-white font-semibold">{size} devices</p>
                  )}
                  <p className="text-gray-500 text-xs mt-1">Roll out after health check</p>
                </div>
              ))}
            </div>
          </div>

          {selectedPlan.devices_affected && selectedPlan.devices_affected.length > 0 && (
            <div className="mb-6">
              <h3 className="text-lg font-semibold text-white mb-4">Affected Devices</h3>
              <div className="bg-slate-700 p-4 rounded max-h-48 overflow-y-auto">
                <div className="space-y-2">
                  {selectedPlan.devices_affected.map((device, idx) => (
                    <div key={idx} className="text-gray-300 text-sm">
                      • {device}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {selectedPlan.notes && (
            <div className="mb-6">
              <h3 className="text-lg font-semibold text-white mb-4">AI Strategy Notes</h3>
              <div className="bg-slate-700 p-4 rounded">
                <p className="text-gray-300 text-sm leading-relaxed">
                  {selectedPlan.notes}
                </p>
              </div>
            </div>
          )}

          {selectedPlan.ticket_id && (
            <div className="mb-6">
              <h3 className="text-lg font-semibold text-white mb-4">Ticket Information</h3>
              <div className="bg-slate-700 p-4 rounded">
                <p className="text-gray-300 text-sm">
                  <span className="font-semibold">Ticket ID:</span> {selectedPlan.ticket_id}
                </p>
              </div>
            </div>
          )}

          <div className="space-y-3">
            {editMode ? (
              <div className="flex gap-3">
                <button
                  onClick={saveEdit}
                  className="flex-1 bg-green-600 hover:bg-green-700 text-white font-medium py-2 px-4 rounded transition-colors"
                >
                  ✓ Save Changes
                </button>
                <button
                  onClick={() => setEditMode(false)}
                  className="flex-1 bg-slate-600 hover:bg-slate-700 text-white font-medium py-2 px-4 rounded transition-colors"
                >
                  ✕ Cancel
                </button>
              </div>
            ) : (
              <>
                <div className="flex gap-3">
                  <button
                    onClick={() => handleApprove(selectedPlan.plan_id)}
                    className="flex-1 bg-green-600 hover:bg-green-700 text-white font-medium py-2 px-4 rounded transition-colors"
                  >
                    ✓ Approve & Execute
                  </button>
                  <button
                    onClick={() => handleReject(selectedPlan.plan_id)}
                    className="flex-1 bg-red-600 hover:bg-red-700 text-white font-medium py-2 px-4 rounded transition-colors"
                  >
                    ✗ Reject
                  </button>
                </div>
                {selectedPlan.status === 'pending_approval' && (
                  <div className="flex gap-3">
                    <button
                      onClick={startEdit}
                      className="flex-1 bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded transition-colors"
                    >
                      ✎ Edit Plan
                    </button>
                    <button
                      onClick={duplicatePlan}
                      disabled={generating}
                      className="flex-1 bg-purple-600 hover:bg-purple-700 disabled:bg-purple-800 text-white font-medium py-2 px-4 rounded transition-colors"
                    >
                      {generating ? '⏳ Duplicating...' : '⎘ Duplicate'}
                    </button>
                  </div>
                )}
                <button
                  onClick={exportPlan}
                  className="w-full bg-slate-700 hover:bg-slate-600 text-white font-medium py-2 px-4 rounded transition-colors"
                >
                  ⬇ Export as JSON
                </button>
              </>
            )}
          </div>
        </div>
      </div>
    );
  }

  // Show history view
  if (showHistory) {
    return (
      <div className="space-y-4">
        <button
          onClick={() => setShowHistory(false)}
          className="text-blue-400 hover:text-blue-300 mb-4 flex items-center gap-2"
        >
          ← Back to Open Plans
        </button>

        <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
          <h2 className="text-xl font-bold text-white mb-4">Plan History</h2>
          <div className="space-y-3">
            {history.length === 0 ? (
              <p className="text-slate-400">No plans yet</p>
            ) : (
              history.map((plan) => (
                <div key={plan.plan_id} className="bg-slate-700 p-3 rounded flex justify-between items-center">
                  <div>
                    <p className="text-white font-semibold">{plan.plan_id}</p>
                    <p className="text-sm text-slate-400">{plan.created_at}</p>
                  </div>
                  <span className={`px-3 py-1 rounded text-sm font-medium ${
                    plan.status === 'pending_approval' ? 'bg-yellow-900 text-yellow-200' :
                    plan.status === 'approved' ? 'bg-green-900 text-green-200' :
                    'bg-red-900 text-red-200'
                  }`}>
                    {plan.status}
                  </span>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex gap-2 mb-4">
        <button
          onClick={generateNewPlan}
          disabled={generating}
          className="bg-blue-600 hover:bg-blue-700 disabled:bg-blue-800 text-white font-medium py-2 px-4 rounded transition-colors"
        >
          {generating ? '⏳ Generating...' : '+ Generate New Plan'}
        </button>
        <button
          onClick={fetchHistory}
          className="bg-slate-700 hover:bg-slate-600 text-white font-medium py-2 px-4 rounded transition-colors"
        >
          📋 View History
        </button>
      </div>

      {plans.length === 0 ? (
        <div className="text-center py-12 text-slate-400">
          <p className="text-lg">No open plans</p>
          <p className="text-sm mt-2">Click "Generate New Plan" to create one</p>
        </div>
      ) : (
        plans.map((plan) => (
          <div
            key={plan.plan_id}
            className="bg-slate-800 border border-slate-700 rounded-lg p-6 hover:border-slate-600 transition-colors cursor-pointer"
            onClick={() => setSelectedPlan(plan)}
          >
            <div className="flex items-start justify-between mb-4">
              <div>
                <h3 className="text-lg font-semibold text-white">{plan.plan_id}</h3>
                <p className="text-sm text-slate-400">Client: {plan.client_id}</p>
              </div>
              <span className="px-3 py-1 bg-yellow-900/30 text-yellow-300 rounded-full text-sm font-medium">
                Pending Approval
              </span>
            </div>

            <div className="grid grid-cols-2 gap-4 mb-4">
              <div>
                <p className="text-sm text-slate-400">Devices Affected</p>
                <p className="text-2xl font-bold text-blue-400">{plan.device_count || 'N/A'}</p>
              </div>
              <div>
                <p className="text-sm text-slate-400">Patches</p>
                <p className="text-lg font-semibold text-slate-200">{plan.patches || 'N/A'}</p>
              </div>
            </div>

            <div className="mb-4">
              <p className="text-sm text-slate-400 mb-2">Strategy</p>
              <p className="text-slate-200 bg-slate-900 rounded p-2">{plan.strategy || 'canary_then_batch'}</p>
            </div>

            <div className="flex gap-3">
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  handleApprove(plan.plan_id);
                }}
                className="flex-1 bg-green-600 hover:bg-green-700 text-white font-medium py-2 px-4 rounded transition-colors"
              >
                ✓ Approve
              </button>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  handleReject(plan.plan_id);
                }}
                className="flex-1 bg-red-600 hover:bg-red-700 text-white font-medium py-2 px-4 rounded transition-colors"
              >
                ✗ Reject
              </button>
            </div>
          </div>
        ))
      )}
    </div>
  );
}

