/**
 * Chat Profile Editor Component
 * Allows editing chat profile configurations with tooltips for each field
 */

import { useState, useEffect } from 'react';
import { apiClient } from '@/lib/api';
import { Tooltip } from './Tooltip';

interface ChatProfileEditorProps {
  profileId: string;
  onClose: () => void;
  onSave: () => void;
}

interface ChatProfileConfig {
  description: string;
  compaction_threshold_tokens: number;
  max_history_turns: number;
  summarization_model: string;
  summarization_max_tokens: number;
  include_summary_in_context: boolean;
  summary_position: string;
  reserve_tokens_for_history: number;
}

const FIELD_TOOLTIPS = {
  description: 'Human-readable description of this chat profile and when to use it.',
  compaction_threshold_tokens: 'Maximum total tokens allowed in chat history before compaction is triggered. When exceeded, older conversation turns are summarized using LLM to reduce token usage while preserving context. Range: 500-10000.',
  max_history_turns: 'Maximum number of conversation turns to keep in full detail before compaction. When exceeded, older turns are summarized. Typically 5-20 turns depending on your use case.',
  summarization_model: 'LLM model to use for summarizing older conversation turns during compaction. Usually a faster, cheaper model like gpt-3.5-turbo is sufficient for summarization.',
  summarization_max_tokens: 'Maximum tokens for the LLM-generated summary of older conversation turns. Controls summary length and detail. Range: 100-1000.',
  include_summary_in_context: 'When enabled, the LLM-generated summary of older turns is included in the context for new queries. Disable to exclude historical context entirely.',
  summary_position: 'Where to place the conversation summary in the context. "before_retrieval" shows conversation history before retrieved documents, "after_retrieval" shows it after.',
  reserve_tokens_for_history: 'Tokens reserved for chat history in the total context budget. Ensures history has guaranteed space and retrieval context is adjusted accordingly. Range: 0-2000.',
};

const FIELD_LABELS = {
  description: 'Description',
  compaction_threshold_tokens: 'Compaction Threshold (tokens)',
  max_history_turns: 'Max History Turns',
  summarization_model: 'Summarization Model',
  summarization_max_tokens: 'Summarization Max Tokens',
  include_summary_in_context: 'Include Summary in Context',
  summary_position: 'Summary Position',
  reserve_tokens_for_history: 'Reserve Tokens for History',
};

export function ChatProfileEditor({ profileId, onClose, onSave }: ChatProfileEditorProps) {
  const [profile, setProfile] = useState<ChatProfileConfig | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadProfile();
  }, [profileId]);

  const loadProfile = async () => {
    try {
      setLoading(true);
      const response = await apiClient.getChatProfile(profileId);
      setProfile(response.profile);
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Failed to load chat profile');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    if (!profile) return;

    try {
      setSaving(true);
      await apiClient.updateChatProfile(profileId, profile);
      onSave();
    } catch (err: any) {
      setError(err.message || 'Failed to save chat profile');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-6">
          <p className="text-gray-600">Loading chat profile...</p>
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
            <h2 className="text-xl font-semibold text-black">Edit Chat Profile</h2>
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

          {/* Compaction Settings Section */}
          <div className="border-t border-gray-200 pt-4">
            <h3 className="text-md font-semibold text-black mb-4">Compaction Settings</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Compaction Threshold Tokens */}
              <div>
                <label className="block text-sm font-medium text-black mb-2">
                  {FIELD_LABELS.compaction_threshold_tokens}
                  <Tooltip content={FIELD_TOOLTIPS.compaction_threshold_tokens}>
                    <span className="ml-2 text-gray-400">ⓘ</span>
                  </Tooltip>
                </label>
                <input
                  type="number"
                  value={profile.compaction_threshold_tokens}
                  onChange={(e) => setProfile({ ...profile, compaction_threshold_tokens: parseInt(e.target.value) || 0 })}
                  min="500"
                  max="10000"
                  step="100"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 text-black"
                />
                <p className="text-xs text-gray-900 mt-1">Range: 500-10000 tokens</p>
              </div>

              {/* Max History Turns */}
              <div>
                <label className="block text-sm font-medium text-black mb-2">
                  {FIELD_LABELS.max_history_turns}
                  <Tooltip content={FIELD_TOOLTIPS.max_history_turns}>
                    <span className="ml-2 text-gray-400">ⓘ</span>
                  </Tooltip>
                </label>
                <input
                  type="number"
                  value={profile.max_history_turns}
                  onChange={(e) => setProfile({ ...profile, max_history_turns: parseInt(e.target.value) || 0 })}
                  min="1"
                  max="50"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 text-black"
                />
                <p className="text-xs text-gray-900 mt-1">Range: 1-50 turns</p>
              </div>
            </div>
          </div>

          {/* Summarization Settings Section */}
          <div className="border-t border-gray-200 pt-4">
            <h3 className="text-md font-semibold text-black mb-4">Summarization Settings</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Summarization Model */}
              <div>
                <label className="block text-sm font-medium text-black mb-2">
                  {FIELD_LABELS.summarization_model}
                  <Tooltip content={FIELD_TOOLTIPS.summarization_model}>
                    <span className="ml-2 text-gray-400">ⓘ</span>
                  </Tooltip>
                </label>
                <select
                  value={profile.summarization_model}
                  onChange={(e) => setProfile({ ...profile, summarization_model: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 text-black"
                >
                  <option value="gpt-3.5-turbo">GPT-3.5 Turbo</option>
                  <option value="gpt-4">GPT-4</option>
                  <option value="gpt-4-turbo">GPT-4 Turbo</option>
                </select>
              </div>

              {/* Summarization Max Tokens */}
              <div>
                <label className="block text-sm font-medium text-black mb-2">
                  {FIELD_LABELS.summarization_max_tokens}
                  <Tooltip content={FIELD_TOOLTIPS.summarization_max_tokens}>
                    <span className="ml-2 text-gray-400">ⓘ</span>
                  </Tooltip>
                </label>
                <input
                  type="number"
                  value={profile.summarization_max_tokens}
                  onChange={(e) => setProfile({ ...profile, summarization_max_tokens: parseInt(e.target.value) || 0 })}
                  min="100"
                  max="1000"
                  step="50"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 text-black"
                />
                <p className="text-xs text-gray-900 mt-1">Range: 100-1000 tokens</p>
              </div>
            </div>
          </div>

          {/* Context Integration Section */}
          <div className="border-t border-gray-200 pt-4">
            <h3 className="text-md font-semibold text-black mb-4">Context Integration</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Summary Position */}
              <div>
                <label className="block text-sm font-medium text-black mb-2">
                  {FIELD_LABELS.summary_position}
                  <Tooltip content={FIELD_TOOLTIPS.summary_position}>
                    <span className="ml-2 text-gray-400">ⓘ</span>
                  </Tooltip>
                </label>
                <select
                  value={profile.summary_position}
                  onChange={(e) => setProfile({ ...profile, summary_position: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 text-black"
                >
                  <option value="before_retrieval">Before Retrieval</option>
                  <option value="after_retrieval">After Retrieval</option>
                </select>
              </div>

              {/* Reserve Tokens for History */}
              <div>
                <label className="block text-sm font-medium text-black mb-2">
                  {FIELD_LABELS.reserve_tokens_for_history}
                  <Tooltip content={FIELD_TOOLTIPS.reserve_tokens_for_history}>
                    <span className="ml-2 text-gray-400">ⓘ</span>
                  </Tooltip>
                </label>
                <input
                  type="number"
                  value={profile.reserve_tokens_for_history}
                  onChange={(e) => setProfile({ ...profile, reserve_tokens_for_history: parseInt(e.target.value) || 0 })}
                  min="0"
                  max="2000"
                  step="100"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 text-black"
                />
                <p className="text-xs text-gray-900 mt-1">Range: 0-2000 tokens</p>
              </div>
            </div>

            {/* Include Summary in Context Toggle */}
            <div className="mt-4 border border-gray-200 rounded-md p-4">
              <label className="flex items-start cursor-pointer">
                <input
                  type="checkbox"
                  checked={profile.include_summary_in_context}
                  onChange={(e) => setProfile({ ...profile, include_summary_in_context: e.target.checked })}
                  className="mt-1 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
                <div className="ml-3">
                  <div className="text-sm font-medium text-black">
                    {FIELD_LABELS.include_summary_in_context}
                    <Tooltip content={FIELD_TOOLTIPS.include_summary_in_context}>
                      <span className="ml-2 text-gray-400">ⓘ</span>
                    </Tooltip>
                  </div>
                  <div className="text-xs text-gray-900 mt-1">Include LLM-generated summary of older turns in context</div>
                </div>
              </label>
            </div>
          </div>

          {/* Configuration Preview */}
          <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
            <h3 className="text-sm font-semibold text-blue-900 mb-2">Configuration Summary</h3>
            <div className="grid grid-cols-2 gap-2 text-xs">
              <div>
                <span className="text-blue-700">Compaction Threshold:</span> <span className="font-mono text-black">{profile.compaction_threshold_tokens} tokens</span>
              </div>
              <div>
                <span className="text-blue-700">Max Turns:</span> <span className="font-mono text-black">{profile.max_history_turns}</span>
              </div>
              <div>
                <span className="text-blue-700">Summary Model:</span> <span className="font-mono text-black">{profile.summarization_model}</span>
              </div>
              <div>
                <span className="text-blue-700">Summary Max Tokens:</span> <span className="font-mono text-black">{profile.summarization_max_tokens}</span>
              </div>
              <div>
                <span className="text-blue-700">Reserved Tokens:</span> <span className="font-mono text-black">{profile.reserve_tokens_for_history}</span>
              </div>
              <div>
                <span className="text-blue-700">Include Summary:</span> <span className="font-mono text-black">{profile.include_summary_in_context ? 'Yes' : 'No'}</span>
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
