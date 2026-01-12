/**
 * Context Profile Editor Component
 * Allows editing context profile configurations with tooltips for each field
 */

import { useState, useEffect } from 'react';
import { apiClient } from '@/lib/api';
import { Tooltip } from './Tooltip';

interface ContextProfileEditorProps {
  profileId: string;
  onClose: () => void;
  onSave: () => void;
}

interface ContextProfileConfig {
  description: string;
  max_context_tokens: number;
  citation_format: string;
  include_page_numbers: boolean;
  include_doc_metadata: boolean;
  redact_pii: boolean;
  pack_strategy: string;
  reserve_tokens_for_query: number;
  reserve_tokens_for_instructions: number;
}

const FIELD_TOOLTIPS = {
  description: 'Human-readable description of this context profile and when to use it.',
  max_context_tokens: 'Maximum number of tokens to include in the context. Controls how much retrieved content is sent to the LLM. Range: 500-10000.',
  citation_format: 'Format for citations in the answer. "inline" uses compact citations, "detailed" includes full metadata.',
  include_page_numbers: 'When enabled, include page numbers in chunk citations for easier reference back to source documents.',
  include_doc_metadata: 'When enabled, include document metadata (form number, state, effective date) in the context pack.',
  redact_pii: 'When enabled, attempt to redact personally identifiable information from the context before sending to LLM.',
  pack_strategy: 'Strategy for packing chunks into context. "rank_ordered" prioritizes by fusion rank, "citation_first" optimizes for citation quality.',
  reserve_tokens_for_query: 'Tokens reserved for the user query in the final prompt. Ensures query fits within model limits. Range: 0-500.',
  reserve_tokens_for_instructions: 'Tokens reserved for system instructions in the final prompt. Range: 0-500.',
};

const FIELD_LABELS = {
  description: 'Description',
  max_context_tokens: 'Max Context Tokens',
  citation_format: 'Citation Format',
  include_page_numbers: 'Include Page Numbers',
  include_doc_metadata: 'Include Document Metadata',
  redact_pii: 'Redact PII',
  pack_strategy: 'Packing Strategy',
  reserve_tokens_for_query: 'Reserve Tokens for Query',
  reserve_tokens_for_instructions: 'Reserve Tokens for Instructions',
};

export function ContextProfileEditor({ profileId, onClose, onSave }: ContextProfileEditorProps) {
  const [profile, setProfile] = useState<ContextProfileConfig | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadProfile();
  }, [profileId]);

  const loadProfile = async () => {
    try {
      setLoading(true);
      const response = await apiClient.getContextProfile(profileId);
      setProfile(response.profile);
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Failed to load context profile');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    if (!profile) return;

    try {
      setSaving(true);
      await apiClient.updateContextProfile(profileId, profile);
      onSave();
    } catch (err: any) {
      setError(err.message || 'Failed to save context profile');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-6">
          <p className="text-gray-600">Loading context profile...</p>
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
            <h2 className="text-xl font-semibold text-black">Edit Context Profile</h2>
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

          {/* Token Budget Section */}
          <div className="border-t border-gray-200 pt-4">
            <h3 className="text-md font-semibold text-black mb-4">Token Budget</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {/* Max Context Tokens */}
              <div>
                <label className="block text-sm font-medium text-black mb-2">
                  {FIELD_LABELS.max_context_tokens}
                  <Tooltip content={FIELD_TOOLTIPS.max_context_tokens}>
                    <span className="ml-2 text-gray-400">ⓘ</span>
                  </Tooltip>
                </label>
                <input
                  type="number"
                  value={profile.max_context_tokens}
                  onChange={(e) => setProfile({ ...profile, max_context_tokens: parseInt(e.target.value) || 0 })}
                  min="500"
                  max="10000"
                  step="100"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 text-black"
                />
                <p className="text-xs text-gray-900 mt-1">Range: 500-10000</p>
              </div>

              {/* Reserve Tokens for Query */}
              <div>
                <label className="block text-sm font-medium text-black mb-2">
                  {FIELD_LABELS.reserve_tokens_for_query}
                  <Tooltip content={FIELD_TOOLTIPS.reserve_tokens_for_query}>
                    <span className="ml-2 text-gray-400">ⓘ</span>
                  </Tooltip>
                </label>
                <input
                  type="number"
                  value={profile.reserve_tokens_for_query}
                  onChange={(e) => setProfile({ ...profile, reserve_tokens_for_query: parseInt(e.target.value) || 0 })}
                  min="0"
                  max="500"
                  step="10"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 text-black"
                />
                <p className="text-xs text-gray-900 mt-1">Range: 0-500</p>
              </div>

              {/* Reserve Tokens for Instructions */}
              <div>
                <label className="block text-sm font-medium text-black mb-2">
                  {FIELD_LABELS.reserve_tokens_for_instructions}
                  <Tooltip content={FIELD_TOOLTIPS.reserve_tokens_for_instructions}>
                    <span className="ml-2 text-gray-400">ⓘ</span>
                  </Tooltip>
                </label>
                <input
                  type="number"
                  value={profile.reserve_tokens_for_instructions}
                  onChange={(e) => setProfile({ ...profile, reserve_tokens_for_instructions: parseInt(e.target.value) || 0 })}
                  min="0"
                  max="500"
                  step="10"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 text-black"
                />
                <p className="text-xs text-gray-900 mt-1">Range: 0-500</p>
              </div>
            </div>
          </div>

          {/* Citation and Packing Section */}
          <div className="border-t border-gray-200 pt-4">
            <h3 className="text-md font-semibold text-black mb-4">Citation & Packing</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Citation Format */}
              <div>
                <label className="block text-sm font-medium text-black mb-2">
                  {FIELD_LABELS.citation_format}
                  <Tooltip content={FIELD_TOOLTIPS.citation_format}>
                    <span className="ml-2 text-gray-400">ⓘ</span>
                  </Tooltip>
                </label>
                <select
                  value={profile.citation_format}
                  onChange={(e) => setProfile({ ...profile, citation_format: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 text-black"
                >
                  <option value="inline">Inline</option>
                  <option value="detailed">Detailed</option>
                </select>
              </div>

              {/* Pack Strategy */}
              <div>
                <label className="block text-sm font-medium text-black mb-2">
                  {FIELD_LABELS.pack_strategy}
                  <Tooltip content={FIELD_TOOLTIPS.pack_strategy}>
                    <span className="ml-2 text-gray-400">ⓘ</span>
                  </Tooltip>
                </label>
                <select
                  value={profile.pack_strategy}
                  onChange={(e) => setProfile({ ...profile, pack_strategy: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 text-black"
                >
                  <option value="rank_ordered">Rank Ordered</option>
                  <option value="citation_first">Citation First</option>
                </select>
              </div>
            </div>
          </div>

          {/* Boolean Options Section */}
          <div className="border-t border-gray-200 pt-4">
            <h3 className="text-md font-semibold text-black mb-4">Content Options</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Include Page Numbers */}
              <div className="border border-gray-200 rounded-md p-4">
                <label className="flex items-start cursor-pointer">
                  <input
                    type="checkbox"
                    checked={profile.include_page_numbers}
                    onChange={(e) => setProfile({ ...profile, include_page_numbers: e.target.checked })}
                    className="mt-1 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                  <div className="ml-3">
                    <div className="text-sm font-medium text-black">
                      {FIELD_LABELS.include_page_numbers}
                      <Tooltip content={FIELD_TOOLTIPS.include_page_numbers}>
                        <span className="ml-2 text-gray-400">ⓘ</span>
                      </Tooltip>
                    </div>
                    <div className="text-xs text-gray-900 mt-1">Add page numbers to citations</div>
                  </div>
                </label>
              </div>

              {/* Include Doc Metadata */}
              <div className="border border-gray-200 rounded-md p-4">
                <label className="flex items-start cursor-pointer">
                  <input
                    type="checkbox"
                    checked={profile.include_doc_metadata}
                    onChange={(e) => setProfile({ ...profile, include_doc_metadata: e.target.checked })}
                    className="mt-1 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                  <div className="ml-3">
                    <div className="text-sm font-medium text-black">
                      {FIELD_LABELS.include_doc_metadata}
                      <Tooltip content={FIELD_TOOLTIPS.include_doc_metadata}>
                        <span className="ml-2 text-gray-400">ⓘ</span>
                      </Tooltip>
                    </div>
                    <div className="text-xs text-gray-900 mt-1">Include form numbers and dates</div>
                  </div>
                </label>
              </div>

              {/* Redact PII */}
              <div className="border border-gray-200 rounded-md p-4 md:col-span-2">
                <label className="flex items-start cursor-pointer">
                  <input
                    type="checkbox"
                    checked={profile.redact_pii}
                    onChange={(e) => setProfile({ ...profile, redact_pii: e.target.checked })}
                    className="mt-1 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                  <div className="ml-3">
                    <div className="text-sm font-medium text-black">
                      {FIELD_LABELS.redact_pii}
                      <Tooltip content={FIELD_TOOLTIPS.redact_pii}>
                        <span className="ml-2 text-gray-400">ⓘ</span>
                      </Tooltip>
                    </div>
                    <div className="text-xs text-gray-900 mt-1">Redact sensitive personal information</div>
                  </div>
                </label>
              </div>
            </div>
          </div>

          {/* Configuration Preview */}
          <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
            <h3 className="text-sm font-semibold text-blue-900 mb-2">Configuration Summary</h3>
            <div className="grid grid-cols-2 gap-2 text-xs">
              <div>
                <span className="text-blue-700">Max Tokens:</span> <span className="font-mono text-black">{profile.max_context_tokens}</span>
              </div>
              <div>
                <span className="text-blue-700">Citation:</span> <span className="font-mono text-black">{profile.citation_format}</span>
              </div>
              <div>
                <span className="text-blue-700">Pack Strategy:</span> <span className="font-mono text-black">{profile.pack_strategy}</span>
              </div>
              <div>
                <span className="text-blue-700">PII Redaction:</span> <span className="font-mono text-black">{profile.redact_pii ? 'Enabled' : 'Disabled'}</span>
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
