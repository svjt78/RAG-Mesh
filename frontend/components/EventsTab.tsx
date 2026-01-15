/**
 * Events Tab - Real-time event stream with SSE
 */

import { Event } from '@/lib/types';
import { useEffect, useState, useRef } from 'react';
import { apiClient } from '@/lib/api';

interface EventsTabProps {
  runId: string | null;
  events: Event[];
}

interface RunSummary {
  run_id: string;
  status?: string;
  created_at?: number;
}

export function EventsTab({ runId, events }: EventsTabProps) {
  const [isStreaming, setIsStreaming] = useState(false);
  const [runs, setRuns] = useState<RunSummary[]>([]);
  const [loadingRuns, setLoadingRuns] = useState(false);
  const [expandedRuns, setExpandedRuns] = useState<Set<string>>(new Set());
  const [runEvents, setRunEvents] = useState<Map<string, Event[]>>(new Map());
  const [selectedRuns, setSelectedRuns] = useState<Set<string>>(new Set());
  const eventsEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    loadRuns();
  }, []);

  useEffect(() => {
    if (runId) {
      loadRuns();
    }
  }, [runId]);

  // Update events for the current run if it's expanded
  useEffect(() => {
    if (runId && expandedRuns.has(runId)) {
      setRunEvents((prev) => {
        const newMap = new Map(prev);
        newMap.set(runId, events);
        return newMap;
      });
    }
  }, [events, runId, expandedRuns]);

  const loadRuns = async () => {
    try {
      setLoadingRuns(true);
      const data = await apiClient.listRuns();
      const fetchedRuns = data.runs || [];
      const hasCurrentRun = runId && fetchedRuns.some((run: RunSummary) => run.run_id === runId);
      const mergedRuns = hasCurrentRun || !runId
        ? fetchedRuns
        : [
            {
              run_id: runId,
              status: 'running',
              created_at: Date.now() / 1000,
            },
            ...fetchedRuns,
          ];
      setRuns(mergedRuns);
    } catch (err) {
      if (runId) {
        setRuns([
          {
            run_id: runId,
            status: 'running',
            created_at: Date.now() / 1000,
          },
        ]);
      } else {
        setRuns([]);
      }
    } finally {
      setLoadingRuns(false);
    }
  };

  const handleViewRun = async (targetRunId: string) => {
    // Toggle expansion
    if (expandedRuns.has(targetRunId)) {
      // Collapse: remove from expanded set
      setExpandedRuns((prev) => {
        const newSet = new Set(prev);
        newSet.delete(targetRunId);
        return newSet;
      });
    } else {
      // Expand: add to expanded set and fetch events if needed
      setExpandedRuns((prev) => new Set(prev).add(targetRunId));

      // Fetch events if not already cached
      if (!runEvents.has(targetRunId)) {
        if (targetRunId === runId) {
          // Use events from props for current run
          setRunEvents((prev) => {
            const newMap = new Map(prev);
            newMap.set(targetRunId, events);
            return newMap;
          });
        } else {
          // Fetch events for past runs
          try {
            const data = await apiClient.getRunStatus(targetRunId);
            setRunEvents((prev) => {
              const newMap = new Map(prev);
              newMap.set(targetRunId, data.events || []);
              return newMap;
            });
          } catch (err) {
            setRunEvents((prev) => {
              const newMap = new Map(prev);
              newMap.set(targetRunId, []);
              return newMap;
            });
          }
        }
      }
    }
  };

  const handleDeleteRun = async (targetRunId: string) => {
    if (!confirm('Delete this run and all its artifacts?')) return;
    try {
      await apiClient.deleteRun(targetRunId);
      await loadRuns();

      // Clean up expanded state and cached events
      if (expandedRuns.has(targetRunId)) {
        setExpandedRuns((prev) => {
          const newSet = new Set(prev);
          newSet.delete(targetRunId);
          return newSet;
        });
      }
      if (runEvents.has(targetRunId)) {
        setRunEvents((prev) => {
          const newMap = new Map(prev);
          newMap.delete(targetRunId);
          return newMap;
        });
      }
    } catch (err) {
      alert('Failed to delete run.');
    }
  };

  const handleSelectAll = () => {
    if (selectedRuns.size === runs.length) {
      // Deselect all
      setSelectedRuns(new Set());
    } else {
      // Select all
      setSelectedRuns(new Set(runs.map((run) => run.run_id)));
    }
  };

  const handleSelectRun = (runId: string) => {
    setSelectedRuns((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(runId)) {
        newSet.delete(runId);
      } else {
        newSet.add(runId);
      }
      return newSet;
    });
  };

  const handleBulkDelete = async () => {
    if (selectedRuns.size === 0) {
      alert('Please select at least one run to delete.');
      return;
    }

    const confirmMessage = `Are you sure you want to delete ${selectedRuns.size} run${selectedRuns.size > 1 ? 's' : ''} and all their artifacts? This action cannot be undone.`;
    if (!confirm(confirmMessage)) return;

    try {
      // Delete all selected runs
      await Promise.all(
        Array.from(selectedRuns).map((runId) => apiClient.deleteRun(runId))
      );

      // Clean up state
      selectedRuns.forEach((runId) => {
        if (expandedRuns.has(runId)) {
          setExpandedRuns((prev) => {
            const newSet = new Set(prev);
            newSet.delete(runId);
            return newSet;
          });
        }
        if (runEvents.has(runId)) {
          setRunEvents((prev) => {
            const newMap = new Map(prev);
            newMap.delete(runId);
            return newMap;
          });
        }
      });

      // Clear selections and reload
      setSelectedRuns(new Set());
      await loadRuns();
    } catch (err) {
      alert('Failed to delete some runs. Please try again.');
    }
  };

  if (!runId && runs.length === 0 && !loadingRuns) {
    return (
      <div className="text-center py-12 text-gray-500">
        <p>No active run. Execute a query to see real-time events.</p>
      </div>
    );
  }

  const eventTypeColors: Record<string, string> = {
    run_start: 'bg-blue-100 text-blue-800',
    run_complete: 'bg-green-100 text-green-800',
    run_error: 'bg-red-100 text-red-800',
    retrieval_start: 'bg-purple-100 text-purple-800',
    retrieval_complete: 'bg-purple-100 text-purple-800',
    fusion_start: 'bg-indigo-100 text-indigo-800',
    fusion_complete: 'bg-indigo-100 text-indigo-800',
    context_start: 'bg-yellow-100 text-yellow-800',
    context_complete: 'bg-yellow-100 text-yellow-800',
    generation_start: 'bg-pink-100 text-pink-800',
    generation_complete: 'bg-pink-100 text-pink-800',
    judge_start: 'bg-orange-100 text-orange-800',
    judge_complete: 'bg-orange-100 text-orange-800',
  };

  // Render inline events timeline for a specific run
  const renderEventsTimeline = (events: Event[], targetRunId: string) => {
    if (events.length === 0) {
      return (
        <div className="text-center py-8 text-gray-500">
          <p>No events found for this run.</p>
        </div>
      );
    }

    return (
      <div className="bg-gray-50 p-4 border-t border-gray-200">
        <div className="max-h-[400px] overflow-y-auto">
          <div className="space-y-3">
            {events.map((event, idx) => (
              <div key={`${event.run_id}-${event.timestamp}-${idx}`} className="flex gap-3">
                {/* Timeline Line */}
                <div className="flex flex-col items-center">
                  <div className="w-3 h-3 rounded-full bg-blue-600 ring-4 ring-blue-100" />
                  {idx < events.length - 1 && (
                    <div className="w-0.5 h-full bg-gray-200 mt-1" />
                  )}
                </div>

                {/* Event Content */}
                <div className="flex-1 pb-4">
                  <div className="flex items-start justify-between mb-1">
                    <span className={`px-2 py-1 text-xs font-medium rounded ${
                      eventTypeColors[event.event_type] || 'bg-gray-100 text-gray-800'
                    }`}>
                      {event.event_type}
                    </span>
                    <span className="text-xs text-gray-500">
                      {new Date(event.timestamp).toLocaleTimeString()}
                    </span>
                  </div>
                  <div className="text-sm font-medium text-gray-900 mb-1">{event.step}</div>
                  {event.data && Object.keys(event.data).length > 0 && (
                    <details className="mt-2">
                      <summary className="text-xs text-gray-600 cursor-pointer hover:text-gray-900">
                        View Data
                      </summary>
                      <pre className="mt-1 text-xs text-gray-700 bg-white p-2 rounded overflow-x-auto">
                        {JSON.stringify(event.data, null, 2)}
                      </pre>
                    </details>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-lg font-semibold text-gray-900">Event Stream</h2>
          <p className="text-sm text-gray-600">
            {expandedRuns.size === 0
              ? 'Click "View" on an event stream to see its events'
              : `${expandedRuns.size} event ${expandedRuns.size === 1 ? 'stream' : 'streams'} expanded`}
          </p>
        </div>
        <div className="flex items-center gap-2">
          {isStreaming && (
            <span className="flex items-center gap-2 text-sm text-green-600">
              <span className="w-2 h-2 bg-green-600 rounded-full animate-pulse" />
              Streaming
            </span>
          )}
          <span className="text-sm text-gray-500">{runs.length} total runs</span>
        </div>
      </div>

      {/* Run List */}
      <div className="border border-gray-200 rounded-lg bg-white">
        <div className="flex items-center justify-between px-4 py-3 border-b border-gray-200">
          <div className="flex items-center gap-3">
            <input
              type="checkbox"
              checked={runs.length > 0 && selectedRuns.size === runs.length}
              onChange={handleSelectAll}
              className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
              title="Select all runs"
            />
            <h3 className="text-sm font-semibold text-gray-900">Event Streams</h3>
            {selectedRuns.size > 0 && (
              <button
                onClick={handleBulkDelete}
                className="ml-2 px-3 py-1 text-xs font-medium text-white bg-red-600 hover:bg-red-700 rounded transition-colors"
                title={`Delete ${selectedRuns.size} selected run${selectedRuns.size > 1 ? 's' : ''}`}
              >
                Delete Selected ({selectedRuns.size})
              </button>
            )}
          </div>
          <button
            onClick={loadRuns}
            className="text-xs text-blue-600 hover:text-blue-800"
          >
            Refresh
          </button>
        </div>
        <div className="divide-y divide-gray-200">
          {loadingRuns ? (
            <div className="px-4 py-3 text-sm text-gray-500">Loading runs...</div>
          ) : runs.length === 0 ? (
            <div className="px-4 py-3 text-sm text-gray-500">No runs found.</div>
          ) : (
            runs.map((run) => {
              const isExpanded = expandedRuns.has(run.run_id);
              const events = runEvents.get(run.run_id) || [];

              return (
                <div key={run.run_id}>
                  {/* Run Header */}
                  <div className="flex items-center justify-between px-4 py-3">
                    <div className="flex items-center gap-3">
                      <input
                        type="checkbox"
                        checked={selectedRuns.has(run.run_id)}
                        onChange={() => handleSelectRun(run.run_id)}
                        className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                        onClick={(e) => e.stopPropagation()}
                        title="Select this run"
                      />
                      <div>
                        <div className="text-sm text-gray-900">
                          Real-time pipeline events for run: <span className="font-mono">{run.run_id}</span>
                        </div>
                        <div className="text-xs text-gray-500">
                          {run.status || 'unknown'}{run.created_at ? ` • ${new Date(run.created_at * 1000).toLocaleString()}` : ''}
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      <button
                        onClick={() => handleViewRun(run.run_id)}
                        className="inline-flex items-center gap-1 text-xs text-blue-600 hover:text-blue-800"
                        title={isExpanded ? 'Hide event stream' : 'View event stream'}
                      >
                        {isExpanded ? (
                          <>
                            <svg
                              className="w-4 h-4"
                              viewBox="0 0 24 24"
                              fill="none"
                              stroke="currentColor"
                              strokeWidth="2"
                              strokeLinecap="round"
                              strokeLinejoin="round"
                            >
                              <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94" />
                              <path d="M1 1l22 22" />
                              <path d="M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19" />
                            </svg>
                            Hide
                          </>
                        ) : (
                          <>
                            <svg
                              className="w-4 h-4"
                              viewBox="0 0 24 24"
                              fill="none"
                              stroke="currentColor"
                              strokeWidth="2"
                              strokeLinecap="round"
                              strokeLinejoin="round"
                            >
                              <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8Z" />
                              <circle cx="12" cy="12" r="3" />
                            </svg>
                            View
                          </>
                        )}
                      </button>
                      <button
                        onClick={() => handleDeleteRun(run.run_id)}
                        className="inline-flex items-center gap-1 text-xs text-red-600 hover:text-red-800"
                        title="Delete this run"
                      >
                        <svg
                          className="w-4 h-4"
                          viewBox="0 0 24 24"
                          fill="none"
                          stroke="currentColor"
                          strokeWidth="2"
                          strokeLinecap="round"
                          strokeLinejoin="round"
                        >
                          <path d="M3 6h18" />
                          <path d="M8 6V4h8v2" />
                          <path d="M19 6l-1 14H6L5 6" />
                          <path d="M10 11v6" />
                          <path d="M14 11v6" />
                        </svg>
                        Delete
                      </button>
                    </div>
                  </div>

                  {/* Inline Events Timeline */}
                  {isExpanded && renderEventsTimeline(events, run.run_id)}
                </div>
              );
            })
          )}
        </div>
      </div>

      {/* Event Statistics */}
      {expandedRuns.size > 0 && (() => {
        // Aggregate all events from expanded runs
        const allExpandedEvents = Array.from(expandedRuns).flatMap(
          (runId) => runEvents.get(runId) || []
        );

        return (
          <div className="grid grid-cols-4 gap-4">
            <div className="bg-blue-50 rounded-lg p-3">
              <div className="text-lg font-bold text-blue-900">
                {allExpandedEvents.filter((e) => e.event_type.includes('start')).length}
              </div>
              <div className="text-xs text-blue-700">Steps Started</div>
            </div>
            <div className="bg-green-50 rounded-lg p-3">
              <div className="text-lg font-bold text-green-900">
                {allExpandedEvents.filter((e) => e.event_type.includes('complete')).length}
              </div>
              <div className="text-xs text-green-700">Steps Completed</div>
            </div>
            <div className="bg-red-50 rounded-lg p-3">
              <div className="text-lg font-bold text-red-900">
                {allExpandedEvents.filter((e) => e.event_type.includes('error')).length}
              </div>
              <div className="text-xs text-red-700">Errors</div>
            </div>
            <div className="bg-gray-50 rounded-lg p-3">
              <div className="text-lg font-bold text-gray-900">{allExpandedEvents.length}</div>
              <div className="text-xs text-gray-700">Total Events</div>
            </div>
          </div>
        );
      })()}
    </div>
  );
}
