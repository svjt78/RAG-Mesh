/**
 * Workflow Editor Component
 * Allows editing workflow configurations with tooltips for each field
 */

import { useState, useEffect } from 'react';
import { apiClient } from '@/lib/api';
import { Tooltip } from './Tooltip';

interface WorkflowEditorProps {
  workflowId: string;
  onClose: () => void;
  onSave: () => void;
}

interface WorkflowConfig {
  workflow_id: string;
  description: string;
  steps: string[];
  enable_graph_retrieval: boolean;
  enable_reranking: boolean;
  fail_on_judge_block: boolean;
  timeout_per_step_seconds: number;
  max_retry_attempts: number;
}

const AVAILABLE_STEPS = [
  'retrieval_started',
  'vector_search',
  'document_search',
  'graph_search',
  'fusion',
  'reranking',
  'context_compilation',
  'generation',
  'judge_validation',
];

const FIELD_TOOLTIPS = {
  workflow_id: 'Unique identifier for this workflow. Used when executing queries to select this workflow.',
  description: 'Human-readable description explaining what this workflow does and when to use it.',
  steps: 'Ordered list of pipeline steps to execute. Steps run sequentially in the order specified.',
  enable_graph_retrieval: 'When enabled, graph-based retrieval using entity relationships will be performed. Requires graph_search step in the pipeline.',
  enable_reranking: 'When enabled, retrieved results will be reranked for better relevance. Requires reranking step in the pipeline.',
  fail_on_judge_block: 'When enabled, pipeline execution will fail if the judge validation blocks the answer (e.g., hallucination detected). When disabled, blocked answers are still returned with warnings.',
  timeout_per_step_seconds: 'Maximum time (in seconds) allowed for each pipeline step before timing out. Increase for complex operations or slower APIs.',
  max_retry_attempts: 'Number of times to retry a failed step before giving up. Set to 0 for no retries, higher values for more resilience.',
};

const STEP_DESCRIPTIONS: Record<string, string> = {
  retrieval_started: 'Initialization - marks the start of retrieval phase',
  vector_search: 'Semantic search using vector embeddings (FAISS)',
  document_search: 'Keyword-based search using BM25/TF-IDF',
  graph_search: 'Entity relationship traversal using knowledge graph',
  fusion: 'Combines results from multiple retrieval modalities using Weighted RRF',
  reranking: 'Re-scores and re-orders results for better relevance',
  context_compilation: 'Builds context pack with token budgeting and PII redaction',
  generation: 'Generates answer using LLM with retrieved context',
  judge_validation: 'Validates answer quality with 9 different checks',
};

export function WorkflowEditor({ workflowId, onClose, onSave }: WorkflowEditorProps) {
  const [workflow, setWorkflow] = useState<WorkflowConfig | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadWorkflow();
  }, [workflowId]);

  const loadWorkflow = async () => {
    try {
      setLoading(true);
      const response = await apiClient.getWorkflow(workflowId);
      setWorkflow(response.workflow);
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Failed to load workflow');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    if (!workflow) return;

    try {
      setSaving(true);
      await apiClient.updateWorkflow(workflowId, workflow);
      onSave();
    } catch (err: any) {
      setError(err.message || 'Failed to save workflow');
    } finally {
      setSaving(false);
    }
  };

  const handleStepToggle = (step: string) => {
    if (!workflow) return;

    const newSteps = workflow.steps.includes(step)
      ? workflow.steps.filter(s => s !== step)
      : [...workflow.steps, step].sort((a, b) => {
          return AVAILABLE_STEPS.indexOf(a) - AVAILABLE_STEPS.indexOf(b);
        });

    setWorkflow({ ...workflow, steps: newSteps });
  };

  if (loading) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-6">
          <p className="text-gray-600">Loading workflow...</p>
        </div>
      </div>
    );
  }

  if (!workflow) {
    return null;
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4 overflow-y-auto">
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full my-8">
        {/* Header */}
        <div className="border-b border-gray-200 px-6 py-4 flex justify-between items-center">
          <div>
            <h2 className="text-xl font-semibold text-black">Edit Workflow</h2>
            <p className="text-sm text-gray-900 mt-1">{workflowId}</p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 text-2xl leading-none"
            title="Close editor without saving"
          >
            ×
          </button>
        </div>

        {/* Error Display */}
        {error && (
          <div className="mx-6 mt-4 bg-red-50 border border-red-200 rounded-md p-4">
            <p className="text-sm text-red-800">{error}</p>
          </div>
        )}

        {/* Form */}
        <div className="px-6 py-4 space-y-6 max-h-[70vh] overflow-y-auto">
          {/* Workflow ID (Read-only) */}
          <div>
            <label className="block text-sm font-medium text-black mb-2">
              Workflow ID
              <Tooltip content={FIELD_TOOLTIPS.workflow_id}>
                <span className="ml-2 text-gray-400">ⓘ</span>
              </Tooltip>
            </label>
            <input
              type="text"
              value={workflow.workflow_id}
              disabled
              className="w-full px-3 py-2 border border-gray-300 rounded-md bg-gray-100 text-black cursor-not-allowed"
            />
          </div>

          {/* Description */}
          <div>
            <label className="block text-sm font-medium text-black mb-2">
              Description
              <Tooltip content={FIELD_TOOLTIPS.description}>
                <span className="ml-2 text-gray-400">ⓘ</span>
              </Tooltip>
            </label>
            <textarea
              value={workflow.description}
              onChange={(e) => setWorkflow({ ...workflow, description: e.target.value })}
              rows={2}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 text-black"
              placeholder="e.g., Fast workflow with vector-only retrieval"
            />
          </div>

          {/* Pipeline Steps */}
          <div>
            <label className="block text-sm font-medium text-black mb-2">
              Pipeline Steps (in order)
              <Tooltip content={FIELD_TOOLTIPS.steps}>
                <span className="ml-2 text-gray-400">ⓘ</span>
              </Tooltip>
            </label>
            <div className="space-y-2 border border-gray-200 rounded-md p-4 bg-gray-50">
              {AVAILABLE_STEPS.map((step) => (
                <div key={step} className="flex items-start">
                  <input
                    type="checkbox"
                    id={step}
                    checked={workflow.steps.includes(step)}
                    onChange={() => handleStepToggle(step)}
                    className="mt-1 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                  <label htmlFor={step} className="ml-3 flex-1">
                    <div className="text-sm font-medium text-black">{step}</div>
                    <div className="text-xs text-gray-900">{STEP_DESCRIPTIONS[step]}</div>
                  </label>
                </div>
              ))}
            </div>
          </div>

          {/* Boolean Toggles */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Enable Graph Retrieval */}
            <div className="border border-gray-200 rounded-md p-4">
              <label className="flex items-start cursor-pointer">
                <input
                  type="checkbox"
                  checked={workflow.enable_graph_retrieval}
                  onChange={(e) => setWorkflow({ ...workflow, enable_graph_retrieval: e.target.checked })}
                  className="mt-1 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
                <div className="ml-3">
                  <div className="text-sm font-medium text-black">
                    Enable Graph Retrieval
                    <Tooltip content={FIELD_TOOLTIPS.enable_graph_retrieval}>
                      <span className="ml-2 text-gray-400">ⓘ</span>
                    </Tooltip>
                  </div>
                  <div className="text-xs text-gray-900 mt-1">Use knowledge graph for retrieval</div>
                </div>
              </label>
            </div>

            {/* Enable Reranking */}
            <div className="border border-gray-200 rounded-md p-4">
              <label className="flex items-start cursor-pointer">
                <input
                  type="checkbox"
                  checked={workflow.enable_reranking}
                  onChange={(e) => setWorkflow({ ...workflow, enable_reranking: e.target.checked })}
                  className="mt-1 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
                <div className="ml-3">
                  <div className="text-sm font-medium text-black">
                    Enable Reranking
                    <Tooltip content={FIELD_TOOLTIPS.enable_reranking}>
                      <span className="ml-2 text-gray-400">ⓘ</span>
                    </Tooltip>
                  </div>
                  <div className="text-xs text-gray-900 mt-1">Re-score results for better relevance</div>
                </div>
              </label>
            </div>

            {/* Fail on Judge Block */}
            <div className="border border-gray-200 rounded-md p-4">
              <label className="flex items-start cursor-pointer">
                <input
                  type="checkbox"
                  checked={workflow.fail_on_judge_block}
                  onChange={(e) => setWorkflow({ ...workflow, fail_on_judge_block: e.target.checked })}
                  className="mt-1 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
                <div className="ml-3">
                  <div className="text-sm font-medium text-black">
                    Fail on Judge Block
                    <Tooltip content={FIELD_TOOLTIPS.fail_on_judge_block}>
                      <span className="ml-2 text-gray-400">ⓘ</span>
                    </Tooltip>
                  </div>
                  <div className="text-xs text-gray-900 mt-1">Stop if judge blocks answer</div>
                </div>
              </label>
            </div>
          </div>

          {/* Numeric Settings */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Timeout */}
            <div>
              <label className="block text-sm font-medium text-black mb-2">
                Timeout Per Step (seconds)
                <Tooltip content={FIELD_TOOLTIPS.timeout_per_step_seconds}>
                  <span className="ml-2 text-gray-400">ⓘ</span>
                </Tooltip>
              </label>
              <input
                type="number"
                value={workflow.timeout_per_step_seconds}
                onChange={(e) => setWorkflow({ ...workflow, timeout_per_step_seconds: parseInt(e.target.value) || 0 })}
                min="10"
                max="600"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 text-black"
              />
              <p className="text-xs text-gray-900 mt-1">Range: 10-600 seconds</p>
            </div>

            {/* Max Retry Attempts */}
            <div>
              <label className="block text-sm font-medium text-black mb-2">
                Max Retry Attempts
                <Tooltip content={FIELD_TOOLTIPS.max_retry_attempts}>
                  <span className="ml-2 text-gray-400">ⓘ</span>
                </Tooltip>
              </label>
              <input
                type="number"
                value={workflow.max_retry_attempts}
                onChange={(e) => setWorkflow({ ...workflow, max_retry_attempts: parseInt(e.target.value) || 0 })}
                min="0"
                max="5"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 text-black"
              />
              <p className="text-xs text-gray-900 mt-1">Range: 0-5 attempts</p>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="border-t border-gray-200 px-6 py-4 flex justify-end space-x-3">
          <button
            onClick={onClose}
            className="px-4 py-2 border border-gray-300 rounded-md text-black hover:bg-gray-50"
            disabled={saving}
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
            disabled={saving}
          >
            {saving ? 'Saving...' : 'Save Changes'}
          </button>
        </div>
      </div>
    </div>
  );
}
