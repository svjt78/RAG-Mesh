/**
 * Fusion Profile Editor Component
 * Allows editing fusion profile configurations with tooltips for each field
 */

import { useState, useEffect } from 'react';
import { apiClient } from '@/lib/api';
import { Tooltip } from './Tooltip';

interface FusionProfileEditorProps {
  profileId: string;
  onClose: () => void;
  onSave: () => void;
}

interface FusionProfileConfig {
  description: string;
  vector_weight: number;
  document_weight: number;
  graph_weight: number;
  rrf_k: number;
  max_chunks_per_doc: number;
  min_distinct_docs: number;
  dedup_threshold: number;
  apply_diversity_constraints: boolean;
  final_top_k: number;
}

const FIELD_TOOLTIPS = {
  description: 'Human-readable description of this fusion profile strategy and when to use it.',
  vector_weight: 'Weight for vector search results in the fusion ranking. Higher values prioritize semantic similarity. Range: 0-5.',
  document_weight: 'Weight for document/keyword search results. Higher values prioritize exact keyword matches. Range: 0-5.',
  graph_weight: 'Weight for graph traversal results. Higher values prioritize entity relationships and graph structure. Range: 0-5.',
  rrf_k: 'Reciprocal Rank Fusion k parameter. Controls the smoothing of rank-based scores. Typical value: 60. Range: 1-100.',
  max_chunks_per_doc: 'Maximum number of chunks to include from any single document. Prevents over-representation. Range: 1-10.',
  min_distinct_docs: 'Minimum number of distinct documents required in results. Ensures diversity across sources. Range: 1-10.',
  dedup_threshold: 'Similarity threshold for deduplication (0-1). Chunks with similarity above this are considered duplicates. Higher = more aggressive dedup.',
  apply_diversity_constraints: 'When enabled, enforces min_distinct_docs and max_chunks_per_doc constraints to ensure result diversity.',
  final_top_k: 'Final number of chunks to return after fusion and ranking. Range: 1-50.',
};

const FIELD_LABELS = {
  description: 'Description',
  vector_weight: 'Vector Search Weight',
  document_weight: 'Document Search Weight',
  graph_weight: 'Graph Search Weight',
  rrf_k: 'RRF K Parameter',
  max_chunks_per_doc: 'Max Chunks Per Document',
  min_distinct_docs: 'Min Distinct Documents',
  dedup_threshold: 'Deduplication Threshold',
  apply_diversity_constraints: 'Apply Diversity Constraints',
  final_top_k: 'Final Top K Results',
};

export function FusionProfileEditor({ profileId, onClose, onSave }: FusionProfileEditorProps) {
  const [profile, setProfile] = useState<FusionProfileConfig | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadProfile();
  }, [profileId]);

  const loadProfile = async () => {
    try {
      setLoading(true);
      const response = await apiClient.getFusionProfile(profileId);
      setProfile(response.profile);
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Failed to load fusion profile');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    if (!profile) return;

    try {
      setSaving(true);
      await apiClient.updateFusionProfile(profileId, profile);
      onSave();
    } catch (err: any) {
      setError(err.message || 'Failed to save fusion profile');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-6">
          <p className="text-gray-600">Loading fusion profile...</p>
        </div>
      </div>
    );
  }

  if (!profile) {
    return null;
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4 overflow-y-auto">
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full my-8">
        {/* Header */}
        <div className="border-b border-gray-200 px-6 py-4 flex justify-between items-center">
          <div>
            <h2 className="text-xl font-semibold text-black">Edit Fusion Profile</h2>
            <p className="text-sm text-gray-900 mt-1">{profileId}</p>
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
          {/* Description */}
          <div>
            <label className="block text-sm font-medium text-black mb-2">
              {FIELD_LABELS.description}
              <Tooltip content={FIELD_TOOLTIPS.description}>
                <span className="ml-2 text-gray-400">ⓘ</span>
              </Tooltip>
            </label>
            <input
              type="text"
              value={profile.description}
              onChange={(e) => setProfile({ ...profile, description: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 text-black"
            />
          </div>

          {/* Modality Weights Section */}
          <div className="border-t border-gray-200 pt-4">
            <h3 className="text-md font-semibold text-black mb-4">Modality Weights</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {/* Vector Weight */}
              <div>
                <label className="block text-sm font-medium text-black mb-2">
                  {FIELD_LABELS.vector_weight}
                  <Tooltip content={FIELD_TOOLTIPS.vector_weight}>
                    <span className="ml-2 text-gray-400">ⓘ</span>
                  </Tooltip>
                </label>
                <input
                  type="number"
                  value={profile.vector_weight}
                  onChange={(e) => setProfile({ ...profile, vector_weight: parseFloat(e.target.value) || 0 })}
                  min="0"
                  max="5"
                  step="0.1"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 text-black"
                />
                <p className="text-xs text-gray-900 mt-1">Range: 0-5</p>
              </div>

              {/* Document Weight */}
              <div>
                <label className="block text-sm font-medium text-black mb-2">
                  {FIELD_LABELS.document_weight}
                  <Tooltip content={FIELD_TOOLTIPS.document_weight}>
                    <span className="ml-2 text-gray-400">ⓘ</span>
                  </Tooltip>
                </label>
                <input
                  type="number"
                  value={profile.document_weight}
                  onChange={(e) => setProfile({ ...profile, document_weight: parseFloat(e.target.value) || 0 })}
                  min="0"
                  max="5"
                  step="0.1"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 text-black"
                />
                <p className="text-xs text-gray-900 mt-1">Range: 0-5</p>
              </div>

              {/* Graph Weight */}
              <div>
                <label className="block text-sm font-medium text-black mb-2">
                  {FIELD_LABELS.graph_weight}
                  <Tooltip content={FIELD_TOOLTIPS.graph_weight}>
                    <span className="ml-2 text-gray-400">ⓘ</span>
                  </Tooltip>
                </label>
                <input
                  type="number"
                  value={profile.graph_weight}
                  onChange={(e) => setProfile({ ...profile, graph_weight: parseFloat(e.target.value) || 0 })}
                  min="0"
                  max="5"
                  step="0.1"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 text-black"
                />
                <p className="text-xs text-gray-900 mt-1">Range: 0-5</p>
              </div>
            </div>
          </div>

          {/* Fusion Parameters Section */}
          <div className="border-t border-gray-200 pt-4">
            <h3 className="text-md font-semibold text-black mb-4">Fusion Parameters</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* RRF K */}
              <div>
                <label className="block text-sm font-medium text-black mb-2">
                  {FIELD_LABELS.rrf_k}
                  <Tooltip content={FIELD_TOOLTIPS.rrf_k}>
                    <span className="ml-2 text-gray-400">ⓘ</span>
                  </Tooltip>
                </label>
                <input
                  type="number"
                  value={profile.rrf_k}
                  onChange={(e) => setProfile({ ...profile, rrf_k: parseInt(e.target.value) || 0 })}
                  min="1"
                  max="100"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 text-black"
                />
                <p className="text-xs text-gray-900 mt-1">Range: 1-100 (typical: 60)</p>
              </div>

              {/* Final Top K */}
              <div>
                <label className="block text-sm font-medium text-black mb-2">
                  {FIELD_LABELS.final_top_k}
                  <Tooltip content={FIELD_TOOLTIPS.final_top_k}>
                    <span className="ml-2 text-gray-400">ⓘ</span>
                  </Tooltip>
                </label>
                <input
                  type="number"
                  value={profile.final_top_k}
                  onChange={(e) => setProfile({ ...profile, final_top_k: parseInt(e.target.value) || 0 })}
                  min="1"
                  max="50"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 text-black"
                />
                <p className="text-xs text-gray-900 mt-1">Range: 1-50</p>
              </div>

              {/* Dedup Threshold */}
              <div>
                <label className="block text-sm font-medium text-black mb-2">
                  {FIELD_LABELS.dedup_threshold}
                  <Tooltip content={FIELD_TOOLTIPS.dedup_threshold}>
                    <span className="ml-2 text-gray-400">ⓘ</span>
                  </Tooltip>
                </label>
                <input
                  type="number"
                  value={profile.dedup_threshold}
                  onChange={(e) => setProfile({ ...profile, dedup_threshold: parseFloat(e.target.value) || 0 })}
                  min="0"
                  max="1"
                  step="0.01"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 text-black"
                />
                <p className="text-xs text-gray-900 mt-1">Range: 0-1 (higher = more aggressive)</p>
              </div>
            </div>
          </div>

          {/* Diversity Constraints Section */}
          <div className="border-t border-gray-200 pt-4">
            <h3 className="text-md font-semibold text-black mb-4">Diversity Constraints</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Max Chunks Per Doc */}
              <div>
                <label className="block text-sm font-medium text-black mb-2">
                  {FIELD_LABELS.max_chunks_per_doc}
                  <Tooltip content={FIELD_TOOLTIPS.max_chunks_per_doc}>
                    <span className="ml-2 text-gray-400">ⓘ</span>
                  </Tooltip>
                </label>
                <input
                  type="number"
                  value={profile.max_chunks_per_doc}
                  onChange={(e) => setProfile({ ...profile, max_chunks_per_doc: parseInt(e.target.value) || 0 })}
                  min="1"
                  max="10"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 text-black"
                />
                <p className="text-xs text-gray-900 mt-1">Range: 1-10</p>
              </div>

              {/* Min Distinct Docs */}
              <div>
                <label className="block text-sm font-medium text-black mb-2">
                  {FIELD_LABELS.min_distinct_docs}
                  <Tooltip content={FIELD_TOOLTIPS.min_distinct_docs}>
                    <span className="ml-2 text-gray-400">ⓘ</span>
                  </Tooltip>
                </label>
                <input
                  type="number"
                  value={profile.min_distinct_docs}
                  onChange={(e) => setProfile({ ...profile, min_distinct_docs: parseInt(e.target.value) || 0 })}
                  min="1"
                  max="10"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 text-black"
                />
                <p className="text-xs text-gray-900 mt-1">Range: 1-10</p>
              </div>
            </div>

            {/* Apply Diversity Constraints Toggle */}
            <div className="mt-4 border border-gray-200 rounded-md p-4">
              <label className="flex items-start cursor-pointer">
                <input
                  type="checkbox"
                  checked={profile.apply_diversity_constraints}
                  onChange={(e) => setProfile({ ...profile, apply_diversity_constraints: e.target.checked })}
                  className="mt-1 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
                <div className="ml-3">
                  <div className="text-sm font-medium text-black">
                    {FIELD_LABELS.apply_diversity_constraints}
                    <Tooltip content={FIELD_TOOLTIPS.apply_diversity_constraints}>
                      <span className="ml-2 text-gray-400">ⓘ</span>
                    </Tooltip>
                  </div>
                  <div className="text-xs text-gray-900 mt-1">Enforce diversity constraints</div>
                </div>
              </label>
            </div>
          </div>

          {/* Configuration Preview */}
          <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
            <h3 className="text-sm font-semibold text-blue-900 mb-2">Configuration Summary</h3>
            <div className="grid grid-cols-2 gap-2 text-xs">
              <div>
                <span className="text-blue-700">Weights:</span> <span className="font-mono text-black">V:{profile.vector_weight} D:{profile.document_weight} G:{profile.graph_weight}</span>
              </div>
              <div>
                <span className="text-blue-700">RRF K:</span> <span className="font-mono text-black">{profile.rrf_k}</span>
              </div>
              <div>
                <span className="text-blue-700">Final Top-K:</span> <span className="font-mono text-black">{profile.final_top_k}</span>
              </div>
              <div>
                <span className="text-blue-700">Dedup:</span> <span className="font-mono text-black">{profile.dedup_threshold}</span>
              </div>
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
