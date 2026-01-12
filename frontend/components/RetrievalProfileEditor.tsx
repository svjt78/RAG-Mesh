/**
 * Retrieval Profile Editor Component
 * Allows editing retrieval profile configurations with tooltips for each field
 */

import { useState, useEffect } from 'react';
import { apiClient } from '@/lib/api';
import { Tooltip } from './Tooltip';

interface RetrievalProfileEditorProps {
  profileId: string;
  onClose: () => void;
  onSave: () => void;
}

interface RetrievalProfileConfig {
  description: string;
  vector_k: number;
  vector_threshold: number;
  doc_k: number;
  doc_boost_exact_match: number;
  doc_boost_form_number: number;
  doc_boost_defined_term: number;
  graph_max_hops: number;
  graph_entity_types: string[];
}

const FIELD_TOOLTIPS = {
  description: 'Brief description of this retrieval profile and its intended use case.',
  vector_k: 'Number of top results to retrieve from semantic vector search. Higher values cast a wider net but may include less relevant results. Recommended: 10-25 results.',
  vector_threshold: 'Minimum similarity score (0-1) for vector search results. Higher thresholds ensure more relevant results but may miss edge cases. Recommended: 0.65-0.85.',
  doc_k: 'Number of top results to retrieve from keyword-based document search (BM25/TF-IDF). Complements vector search with exact term matching. Recommended: 5-15 results.',
  doc_boost_exact_match: 'Multiplier applied to document search scores when query terms match exactly. Values > 1 prioritize precise keyword matches. Recommended: 1.2-2.0.',
  doc_boost_form_number: 'Multiplier applied when document contains form numbers or policy identifiers. Useful for insurance/legal documents. Recommended: 1.3-2.5.',
  doc_boost_defined_term: 'Multiplier applied when document contains defined terms or glossary entries. Helps surface definitional content. Recommended: 1.2-2.0.',
  graph_max_hops: 'Maximum number of relationship hops to traverse in graph search. Higher values explore more connections but increase latency. Recommended: 1-3 hops.',
  graph_entity_types: 'List of entity types to consider during graph traversal (e.g., Coverage, Exclusion, Definition). Leave empty to include all entity types.',
};

const FIELD_LABELS = {
  description: 'Profile Description',
  vector_k: 'Vector Search Top-K',
  vector_threshold: 'Vector Similarity Threshold',
  doc_k: 'Document Search Top-K',
  doc_boost_exact_match: 'Exact Match Boost',
  doc_boost_form_number: 'Form Number Boost',
  doc_boost_defined_term: 'Defined Term Boost',
  graph_max_hops: 'Graph Max Hops',
  graph_entity_types: 'Graph Entity Types',
};

export function RetrievalProfileEditor({ profileId, onClose, onSave }: RetrievalProfileEditorProps) {
  const [profile, setProfile] = useState<RetrievalProfileConfig | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [entityTypeInput, setEntityTypeInput] = useState('');

  useEffect(() => {
    loadProfile();
  }, [profileId]);

  const loadProfile = async () => {
    try {
      setLoading(true);
      const response = await apiClient.getRetrievalProfile(profileId);
      setProfile(response.profile);
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Failed to load retrieval profile');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    if (!profile) return;

    try {
      setSaving(true);
      await apiClient.updateRetrievalProfile(profileId, profile);
      onSave();
    } catch (err: any) {
      setError(err.message || 'Failed to save retrieval profile');
    } finally {
      setSaving(false);
    }
  };

  const handleAddEntityType = () => {
    if (!profile || !entityTypeInput.trim()) return;

    const trimmedInput = entityTypeInput.trim();
    if (!profile.graph_entity_types.includes(trimmedInput)) {
      setProfile({
        ...profile,
        graph_entity_types: [...profile.graph_entity_types, trimmedInput]
      });
    }
    setEntityTypeInput('');
  };

  const handleRemoveEntityType = (index: number) => {
    if (!profile) return;
    setProfile({
      ...profile,
      graph_entity_types: profile.graph_entity_types.filter((_, i) => i !== index)
    });
  };

  if (loading) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-6">
          <p className="text-gray-600">Loading retrieval profile...</p>
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
            <h2 className="text-xl font-semibold text-black">Edit Retrieval Profile</h2>
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
              placeholder="Brief description of this profile"
            />
          </div>

          {/* Vector Search Section */}
          <div className="border-t pt-4">
            <h3 className="text-md font-semibold text-black mb-4">Vector Search Configuration</h3>

            {/* Vector K */}
            <div className="mb-4">
              <label className="block text-sm font-medium text-black mb-2">
                {FIELD_LABELS.vector_k}
                <Tooltip content={FIELD_TOOLTIPS.vector_k}>
                  <span className="ml-2 text-gray-400">ⓘ</span>
                </Tooltip>
              </label>
              <input
                type="number"
                value={profile.vector_k}
                onChange={(e) => setProfile({ ...profile, vector_k: parseInt(e.target.value) || 0 })}
                min="1"
                max="100"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 text-black"
              />
              <p className="text-xs text-gray-900 mt-1">Range: 1-100 results</p>
            </div>

            {/* Vector Threshold */}
            <div>
              <label className="block text-sm font-medium text-black mb-2">
                {FIELD_LABELS.vector_threshold}
                <Tooltip content={FIELD_TOOLTIPS.vector_threshold}>
                  <span className="ml-2 text-gray-400">ⓘ</span>
                </Tooltip>
              </label>
              <input
                type="number"
                value={profile.vector_threshold}
                onChange={(e) => setProfile({ ...profile, vector_threshold: parseFloat(e.target.value) || 0 })}
                min="0"
                max="1"
                step="0.05"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 text-black"
              />
              <p className="text-xs text-gray-900 mt-1">Range: 0.0-1.0 (higher = more strict)</p>
            </div>
          </div>

          {/* Document Search Section */}
          <div className="border-t pt-4">
            <h3 className="text-md font-semibold text-black mb-4">Document Search Configuration</h3>

            {/* Doc K */}
            <div className="mb-4">
              <label className="block text-sm font-medium text-black mb-2">
                {FIELD_LABELS.doc_k}
                <Tooltip content={FIELD_TOOLTIPS.doc_k}>
                  <span className="ml-2 text-gray-400">ⓘ</span>
                </Tooltip>
              </label>
              <input
                type="number"
                value={profile.doc_k}
                onChange={(e) => setProfile({ ...profile, doc_k: parseInt(e.target.value) || 0 })}
                min="1"
                max="100"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 text-black"
              />
              <p className="text-xs text-gray-900 mt-1">Range: 1-100 results</p>
            </div>

            {/* Boost Factors Grid */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {/* Exact Match Boost */}
              <div>
                <label className="block text-sm font-medium text-black mb-2">
                  {FIELD_LABELS.doc_boost_exact_match}
                  <Tooltip content={FIELD_TOOLTIPS.doc_boost_exact_match}>
                    <span className="ml-2 text-gray-400">ⓘ</span>
                  </Tooltip>
                </label>
                <input
                  type="number"
                  value={profile.doc_boost_exact_match}
                  onChange={(e) => setProfile({ ...profile, doc_boost_exact_match: parseFloat(e.target.value) || 1 })}
                  min="1"
                  max="5"
                  step="0.1"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 text-black"
                />
                <p className="text-xs text-gray-900 mt-1">Range: 1.0-5.0</p>
              </div>

              {/* Form Number Boost */}
              <div>
                <label className="block text-sm font-medium text-black mb-2">
                  {FIELD_LABELS.doc_boost_form_number}
                  <Tooltip content={FIELD_TOOLTIPS.doc_boost_form_number}>
                    <span className="ml-2 text-gray-400">ⓘ</span>
                  </Tooltip>
                </label>
                <input
                  type="number"
                  value={profile.doc_boost_form_number}
                  onChange={(e) => setProfile({ ...profile, doc_boost_form_number: parseFloat(e.target.value) || 1 })}
                  min="1"
                  max="5"
                  step="0.1"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 text-black"
                />
                <p className="text-xs text-gray-900 mt-1">Range: 1.0-5.0</p>
              </div>

              {/* Defined Term Boost */}
              <div>
                <label className="block text-sm font-medium text-black mb-2">
                  {FIELD_LABELS.doc_boost_defined_term}
                  <Tooltip content={FIELD_TOOLTIPS.doc_boost_defined_term}>
                    <span className="ml-2 text-gray-400">ⓘ</span>
                  </Tooltip>
                </label>
                <input
                  type="number"
                  value={profile.doc_boost_defined_term}
                  onChange={(e) => setProfile({ ...profile, doc_boost_defined_term: parseFloat(e.target.value) || 1 })}
                  min="1"
                  max="5"
                  step="0.1"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 text-black"
                />
                <p className="text-xs text-gray-900 mt-1">Range: 1.0-5.0</p>
              </div>
            </div>
          </div>

          {/* Graph Search Section */}
          <div className="border-t pt-4">
            <h3 className="text-md font-semibold text-black mb-4">Graph Search Configuration</h3>

            {/* Graph Max Hops */}
            <div className="mb-4">
              <label className="block text-sm font-medium text-black mb-2">
                {FIELD_LABELS.graph_max_hops}
                <Tooltip content={FIELD_TOOLTIPS.graph_max_hops}>
                  <span className="ml-2 text-gray-400">ⓘ</span>
                </Tooltip>
              </label>
              <input
                type="number"
                value={profile.graph_max_hops}
                onChange={(e) => setProfile({ ...profile, graph_max_hops: parseInt(e.target.value) || 0 })}
                min="0"
                max="5"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 text-black"
              />
              <p className="text-xs text-gray-900 mt-1">Range: 0-5 hops (0 disables graph search)</p>
            </div>

            {/* Graph Entity Types */}
            <div>
              <label className="block text-sm font-medium text-black mb-2">
                {FIELD_LABELS.graph_entity_types}
                <Tooltip content={FIELD_TOOLTIPS.graph_entity_types}>
                  <span className="ml-2 text-gray-400">ⓘ</span>
                </Tooltip>
              </label>

              {/* Entity Type Input */}
              <div className="flex gap-2 mb-2">
                <input
                  type="text"
                  value={entityTypeInput}
                  onChange={(e) => setEntityTypeInput(e.target.value)}
                  onKeyPress={(e) => {
                    if (e.key === 'Enter') {
                      e.preventDefault();
                      handleAddEntityType();
                    }
                  }}
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 text-black"
                  placeholder="Add entity type (e.g., Coverage, Exclusion)"
                />
                <button
                  type="button"
                  onClick={handleAddEntityType}
                  className="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700"
                >
                  Add
                </button>
              </div>

              {/* Entity Type Tags */}
              <div className="flex flex-wrap gap-2">
                {profile.graph_entity_types.length === 0 ? (
                  <p className="text-xs text-gray-500 italic">No entity types specified (all types will be included)</p>
                ) : (
                  profile.graph_entity_types.map((type, index) => (
                    <span
                      key={index}
                      className="inline-flex items-center px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm"
                    >
                      {type}
                      <button
                        type="button"
                        onClick={() => handleRemoveEntityType(index)}
                        className="ml-2 text-blue-600 hover:text-blue-800 font-bold"
                      >
                        ×
                      </button>
                    </span>
                  ))
                )}
              </div>
            </div>
          </div>

          {/* Configuration Preview */}
          <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
            <h3 className="text-sm font-semibold text-blue-900 mb-2">Configuration Summary</h3>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-2 text-xs">
              <div>
                <span className="text-blue-700">Vector Top-K:</span> <span className="font-mono text-black">{profile.vector_k}</span>
              </div>
              <div>
                <span className="text-blue-700">Vector Threshold:</span> <span className="font-mono text-black">{profile.vector_threshold}</span>
              </div>
              <div>
                <span className="text-blue-700">Doc Top-K:</span> <span className="font-mono text-black">{profile.doc_k}</span>
              </div>
              <div>
                <span className="text-blue-700">Graph Hops:</span> <span className="font-mono text-black">{profile.graph_max_hops}</span>
              </div>
              <div>
                <span className="text-blue-700">Entity Types:</span> <span className="font-mono text-black">{profile.graph_entity_types.length || 'All'}</span>
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
