/**
 * Rerank Profile Editor Component
 * Allows editing reranking profile configurations with tooltips for each field
 */

import { useState, useEffect } from 'react';
import { apiClient } from '@/lib/api';
import { Tooltip } from './Tooltip';

interface RerankProfileEditorProps {
  profileId: string;
  onClose: () => void;
  onSave: () => void;
}

interface RerankProfileConfig {
  description: string;
  enabled: boolean;
  model: string;
  max_chunks: number;
  chunk_char_limit: number;
  temperature: number;
  prompt_template: string;
}

const FIELD_TOOLTIPS = {
  description: 'Human-readable description of this reranking profile and when to use it.',
  enabled: 'When enabled, the workflow can use an LLM to rerank fused results. This is optional and may be expensive.',
  model: 'Model name used for reranking (must exist in models.json).',
  max_chunks: 'Maximum number of fused chunks sent to the LLM for reranking. Range: 1-200.',
  chunk_char_limit: 'Maximum characters per chunk included in the reranking prompt. Range: 100-2000.',
  temperature: 'Sampling temperature for reranking. Lower values give more deterministic rankings. Range: 0-1.',
  prompt_template: 'Prompt template with {query} and {chunks} placeholders.'
};

const FIELD_LABELS = {
  description: 'Description',
  enabled: 'Enable LLM Reranking',
  model: 'Reranking Model',
  max_chunks: 'Max Chunks',
  chunk_char_limit: 'Chunk Character Limit',
  temperature: 'Temperature',
  prompt_template: 'Prompt Template'
};

export function RerankProfileEditor({ profileId, onClose, onSave }: RerankProfileEditorProps) {
  const [profile, setProfile] = useState<RerankProfileConfig | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadProfile();
  }, [profileId]);

  const loadProfile = async () => {
    try {
      setLoading(true);
      const response = await apiClient.getRerankingProfile(profileId);
      setProfile(response.profile);
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Failed to load reranking profile');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    if (!profile) return;

    try {
      setSaving(true);
      await apiClient.updateRerankingProfile(profileId, profile);
      onSave();
    } catch (err: any) {
      setError(err.message || 'Failed to save reranking profile');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-6">
          <p className="text-gray-600">Loading reranking profile...</p>
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
            <h2 className="text-xl font-semibold text-black">Edit Reranking Profile</h2>
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

          {/* Reranking Controls */}
          <div className="border-t border-gray-200 pt-4">
            <h3 className="text-md font-semibold text-black mb-4">Reranking Controls</h3>
            <div className="border border-gray-200 rounded-md p-4">
              <label className="flex items-start cursor-pointer">
                <input
                  type="checkbox"
                  checked={profile.enabled}
                  onChange={(e) => setProfile({ ...profile, enabled: e.target.checked })}
                  className="mt-1 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
                <div className="ml-3">
                  <div className="text-sm font-medium text-black">
                    {FIELD_LABELS.enabled}
                    <Tooltip content={FIELD_TOOLTIPS.enabled}>
                      <span className="ml-2 text-gray-400">ⓘ</span>
                    </Tooltip>
                  </div>
                  <div className="text-xs text-gray-900 mt-1">Allow LLM reranking for supported workflows</div>
                </div>
              </label>
            </div>
          </div>

          {/* Model and Limits */}
          <div className="border-t border-gray-200 pt-4">
            <h3 className="text-md font-semibold text-black mb-4">Model & Limits</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Model */}
              <div>
                <label className="block text-sm font-medium text-black mb-2">
                  {FIELD_LABELS.model}
                  <Tooltip content={FIELD_TOOLTIPS.model}>
                    <span className="ml-2 text-gray-400">ⓘ</span>
                  </Tooltip>
                </label>
                <input
                  type="text"
                  value={profile.model}
                  onChange={(e) => setProfile({ ...profile, model: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 text-black"
                />
              </div>

              {/* Temperature */}
              <div>
                <label className="block text-sm font-medium text-black mb-2">
                  {FIELD_LABELS.temperature}
                  <Tooltip content={FIELD_TOOLTIPS.temperature}>
                    <span className="ml-2 text-gray-400">ⓘ</span>
                  </Tooltip>
                </label>
                <input
                  type="number"
                  value={profile.temperature}
                  onChange={(e) => setProfile({ ...profile, temperature: parseFloat(e.target.value) || 0 })}
                  min="0"
                  max="1"
                  step="0.1"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 text-black"
                />
                <p className="text-xs text-gray-900 mt-1">Range: 0-1</p>
              </div>

              {/* Max Chunks */}
              <div>
                <label className="block text-sm font-medium text-black mb-2">
                  {FIELD_LABELS.max_chunks}
                  <Tooltip content={FIELD_TOOLTIPS.max_chunks}>
                    <span className="ml-2 text-gray-400">ⓘ</span>
                  </Tooltip>
                </label>
                <input
                  type="number"
                  value={profile.max_chunks}
                  onChange={(e) => setProfile({ ...profile, max_chunks: parseInt(e.target.value) || 0 })}
                  min="1"
                  max="200"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 text-black"
                />
                <p className="text-xs text-gray-900 mt-1">Range: 1-200</p>
              </div>

              {/* Chunk Char Limit */}
              <div>
                <label className="block text-sm font-medium text-black mb-2">
                  {FIELD_LABELS.chunk_char_limit}
                  <Tooltip content={FIELD_TOOLTIPS.chunk_char_limit}>
                    <span className="ml-2 text-gray-400">ⓘ</span>
                  </Tooltip>
                </label>
                <input
                  type="number"
                  value={profile.chunk_char_limit}
                  onChange={(e) => setProfile({ ...profile, chunk_char_limit: parseInt(e.target.value) || 0 })}
                  min="100"
                  max="2000"
                  step="50"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 text-black"
                />
                <p className="text-xs text-gray-900 mt-1">Range: 100-2000</p>
              </div>
            </div>
          </div>

          {/* Prompt Template */}
          <div className="border-t border-gray-200 pt-4">
            <h3 className="text-md font-semibold text-black mb-4">Prompt Template</h3>
            <label className="block text-sm font-medium text-black mb-2">
              {FIELD_LABELS.prompt_template}
              <Tooltip content={FIELD_TOOLTIPS.prompt_template}>
                <span className="ml-2 text-gray-400">ⓘ</span>
              </Tooltip>
            </label>
            <textarea
              value={profile.prompt_template}
              onChange={(e) => setProfile({ ...profile, prompt_template: e.target.value })}
              rows={8}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 text-black font-mono text-xs"
            />
            <p className="text-xs text-gray-900 mt-1">Use {`{query}`} and {`{chunks}`} placeholders.</p>
          </div>

          {/* Configuration Preview */}
          <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
            <h3 className="text-sm font-semibold text-blue-900 mb-2">Configuration Summary</h3>
            <div className="grid grid-cols-2 gap-2 text-xs">
              <div>
                <span className="text-blue-700">Enabled:</span> <span className="font-mono text-black">{profile.enabled ? 'Yes' : 'No'}</span>
              </div>
              <div>
                <span className="text-blue-700">Model:</span> <span className="font-mono text-black">{profile.model}</span>
              </div>
              <div>
                <span className="text-blue-700">Max Chunks:</span> <span className="font-mono text-black">{profile.max_chunks}</span>
              </div>
              <div>
                <span className="text-blue-700">Chunk Limit:</span> <span className="font-mono text-black">{profile.chunk_char_limit}</span>
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
