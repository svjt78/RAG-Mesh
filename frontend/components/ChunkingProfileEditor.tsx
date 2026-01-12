/**
 * Chunking Profile Editor Component
 * Allows editing chunking profile configurations with tooltips for each field
 */

import { useState, useEffect } from 'react';
import { apiClient } from '@/lib/api';
import { Tooltip } from './Tooltip';

interface ChunkingProfileEditorProps {
  profileId: string;
  onClose: () => void;
  onSave: () => void;
}

interface ChunkingProfileConfig {
  chunk_size: number;
  chunk_overlap: number;
  page_aware: boolean;
  max_chunks_per_doc: number | null;
  sentence_aware: boolean;
  min_chunk_size: number;
  preserve_paragraph_boundaries: boolean;
}

const FIELD_TOOLTIPS = {
  chunk_size: 'Maximum number of characters per chunk. Larger chunks provide more context but may reduce retrieval precision. Recommended: 300-1000 characters.',
  chunk_overlap: 'Number of overlapping characters between consecutive chunks. Helps preserve context across chunk boundaries. Typically 10-20% of chunk_size.',
  page_aware: 'When enabled, chunks will not cross page boundaries in PDF documents. Useful for maintaining document structure and citations.',
  max_chunks_per_doc: 'Maximum number of chunks to create per document. Set to null for unlimited. Use to limit processing time for very large documents.',
  sentence_aware: 'When enabled, chunks will break at sentence boundaries when possible, improving readability and retrieval quality.',
  min_chunk_size: 'Minimum number of characters for a valid chunk. Chunks smaller than this will be merged with adjacent chunks. Prevents tiny, low-value chunks.',
  preserve_paragraph_boundaries: 'When enabled, chunks will respect paragraph breaks and avoid splitting paragraphs. Maintains semantic coherence.',
};

const FIELD_LABELS = {
  chunk_size: 'Chunk Size (characters)',
  chunk_overlap: 'Chunk Overlap (characters)',
  page_aware: 'Page Aware',
  max_chunks_per_doc: 'Max Chunks Per Document',
  sentence_aware: 'Sentence Aware',
  min_chunk_size: 'Min Chunk Size (characters)',
  preserve_paragraph_boundaries: 'Preserve Paragraph Boundaries',
};

export function ChunkingProfileEditor({ profileId, onClose, onSave }: ChunkingProfileEditorProps) {
  const [profile, setProfile] = useState<ChunkingProfileConfig | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadProfile();
  }, [profileId]);

  const loadProfile = async () => {
    try {
      setLoading(true);
      const response = await apiClient.getChunkingProfile(profileId);
      setProfile(response.profile);
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Failed to load chunking profile');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    if (!profile) return;

    try {
      setSaving(true);
      await apiClient.updateChunkingProfile(profileId, profile);
      onSave();
    } catch (err: any) {
      setError(err.message || 'Failed to save chunking profile');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-6">
          <p className="text-gray-600">Loading chunking profile...</p>
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
            <h2 className="text-xl font-semibold text-black">Edit Chunking Profile</h2>
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
          {/* Chunk Size */}
          <div>
            <label className="block text-sm font-medium text-black mb-2">
              {FIELD_LABELS.chunk_size}
              <Tooltip content={FIELD_TOOLTIPS.chunk_size}>
                <span className="ml-2 text-gray-400">ⓘ</span>
              </Tooltip>
            </label>
            <input
              type="number"
              value={profile.chunk_size}
              onChange={(e) => setProfile({ ...profile, chunk_size: parseInt(e.target.value) || 0 })}
              min="100"
              max="5000"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 text-black"
            />
            <p className="text-xs text-gray-900 mt-1">Range: 100-5000 characters</p>
          </div>

          {/* Chunk Overlap */}
          <div>
            <label className="block text-sm font-medium text-black mb-2">
              {FIELD_LABELS.chunk_overlap}
              <Tooltip content={FIELD_TOOLTIPS.chunk_overlap}>
                <span className="ml-2 text-gray-400">ⓘ</span>
              </Tooltip>
            </label>
            <input
              type="number"
              value={profile.chunk_overlap}
              onChange={(e) => setProfile({ ...profile, chunk_overlap: parseInt(e.target.value) || 0 })}
              min="0"
              max="1000"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 text-black"
            />
            <p className="text-xs text-gray-900 mt-1">Range: 0-1000 characters (typically 10-20% of chunk size)</p>
          </div>

          {/* Min Chunk Size */}
          <div>
            <label className="block text-sm font-medium text-black mb-2">
              {FIELD_LABELS.min_chunk_size}
              <Tooltip content={FIELD_TOOLTIPS.min_chunk_size}>
                <span className="ml-2 text-gray-400">ⓘ</span>
              </Tooltip>
            </label>
            <input
              type="number"
              value={profile.min_chunk_size}
              onChange={(e) => setProfile({ ...profile, min_chunk_size: parseInt(e.target.value) || 0 })}
              min="10"
              max="1000"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 text-black"
            />
            <p className="text-xs text-gray-900 mt-1">Range: 10-1000 characters</p>
          </div>

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
              value={profile.max_chunks_per_doc ?? ''}
              onChange={(e) => {
                const value = e.target.value === '' ? null : parseInt(e.target.value);
                setProfile({ ...profile, max_chunks_per_doc: value });
              }}
              min="1"
              placeholder="Unlimited"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 text-black"
            />
            <p className="text-xs text-gray-900 mt-1">Leave empty for unlimited</p>
          </div>

          {/* Boolean Toggles */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Page Aware */}
            <div className="border border-gray-200 rounded-md p-4">
              <label className="flex items-start cursor-pointer">
                <input
                  type="checkbox"
                  checked={profile.page_aware}
                  onChange={(e) => setProfile({ ...profile, page_aware: e.target.checked })}
                  className="mt-1 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
                <div className="ml-3">
                  <div className="text-sm font-medium text-black">
                    {FIELD_LABELS.page_aware}
                    <Tooltip content={FIELD_TOOLTIPS.page_aware}>
                      <span className="ml-2 text-gray-400">ⓘ</span>
                    </Tooltip>
                  </div>
                  <div className="text-xs text-gray-900 mt-1">Respect page boundaries</div>
                </div>
              </label>
            </div>

            {/* Sentence Aware */}
            <div className="border border-gray-200 rounded-md p-4">
              <label className="flex items-start cursor-pointer">
                <input
                  type="checkbox"
                  checked={profile.sentence_aware}
                  onChange={(e) => setProfile({ ...profile, sentence_aware: e.target.checked })}
                  className="mt-1 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
                <div className="ml-3">
                  <div className="text-sm font-medium text-black">
                    {FIELD_LABELS.sentence_aware}
                    <Tooltip content={FIELD_TOOLTIPS.sentence_aware}>
                      <span className="ml-2 text-gray-400">ⓘ</span>
                    </Tooltip>
                  </div>
                  <div className="text-xs text-gray-900 mt-1">Break at sentence boundaries</div>
                </div>
              </label>
            </div>

            {/* Preserve Paragraph Boundaries */}
            <div className="border border-gray-200 rounded-md p-4 md:col-span-2">
              <label className="flex items-start cursor-pointer">
                <input
                  type="checkbox"
                  checked={profile.preserve_paragraph_boundaries}
                  onChange={(e) => setProfile({ ...profile, preserve_paragraph_boundaries: e.target.checked })}
                  className="mt-1 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
                <div className="ml-3">
                  <div className="text-sm font-medium text-black">
                    {FIELD_LABELS.preserve_paragraph_boundaries}
                    <Tooltip content={FIELD_TOOLTIPS.preserve_paragraph_boundaries}>
                      <span className="ml-2 text-gray-400">ⓘ</span>
                    </Tooltip>
                  </div>
                  <div className="text-xs text-gray-900 mt-1">Keep paragraphs intact when possible</div>
                </div>
              </label>
            </div>
          </div>

          {/* Configuration Preview */}
          <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
            <h3 className="text-sm font-semibold text-blue-900 mb-2">Configuration Summary</h3>
            <div className="grid grid-cols-2 gap-2 text-xs">
              <div>
                <span className="text-blue-700">Chunk Size:</span> <span className="font-mono text-black">{profile.chunk_size}</span>
              </div>
              <div>
                <span className="text-blue-700">Overlap:</span> <span className="font-mono text-black">{profile.chunk_overlap}</span>
              </div>
              <div>
                <span className="text-blue-700">Min Size:</span> <span className="font-mono text-black">{profile.min_chunk_size}</span>
              </div>
              <div>
                <span className="text-blue-700">Max Chunks:</span> <span className="font-mono text-black">{profile.max_chunks_per_doc ?? 'Unlimited'}</span>
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
