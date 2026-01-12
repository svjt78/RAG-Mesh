/**
 * Judge Profile Editor Component
 * Allows editing judge profile configurations with tooltips for each field
 */

import { useState, useEffect } from 'react';
import { apiClient } from '@/lib/api';
import { Tooltip } from './Tooltip';

interface JudgeProfileEditorProps {
  profileId: string;
  onClose: () => void;
  onSave: () => void;
}

interface CheckConfig {
  enabled: boolean;
  threshold: number;
  hard_fail: boolean;
  description: string;
}

interface JudgeProfileConfig {
  description: string;
  citation_coverage: CheckConfig;
  groundedness: CheckConfig;
  hallucination: CheckConfig;
  relevance: CheckConfig;
  consistency: CheckConfig;
  toxicity: CheckConfig;
  pii_leakage: CheckConfig;
  bias: CheckConfig;
  contradiction: CheckConfig;
}

const CHECK_TOOLTIPS = {
  citation_coverage: 'Verifies that factual claims in the answer are backed by citations to source documents. Higher threshold = more citations required.',
  groundedness: 'Ensures claims in the answer are entailed by (directly supported by) the provided evidence. Prevents unsupported inferences.',
  hallucination: 'Detects fabricated information not present in source documents. LOWER threshold = stricter (less hallucination tolerated).',
  relevance: 'Measures how well the answer addresses the user query. Higher threshold = stricter relevance requirements.',
  consistency: 'Checks for internal consistency within the answer. Detects self-contradictory statements.',
  toxicity: 'Detects toxic or offensive language. LOWER threshold = stricter (less toxicity tolerated).',
  pii_leakage: 'Detects exposure of personally identifiable information. Should typically be 0.0 (zero tolerance).',
  bias: 'Detects biased or discriminatory language. LOWER threshold = stricter (less bias tolerated).',
  contradiction: 'Detects contradictions between the answer and source evidence. LOWER threshold = stricter.',
};

const CHECK_LABELS = {
  citation_coverage: 'Citation Coverage',
  groundedness: 'Groundedness',
  hallucination: 'Hallucination Detection',
  relevance: 'Relevance',
  consistency: 'Internal Consistency',
  toxicity: 'Toxicity Detection',
  pii_leakage: 'PII Leakage Detection',
  bias: 'Bias Detection',
  contradiction: 'Contradiction Detection',
};

const CHECK_KEYS: (keyof Omit<JudgeProfileConfig, 'description'>)[] = [
  'citation_coverage',
  'groundedness',
  'hallucination',
  'relevance',
  'consistency',
  'toxicity',
  'pii_leakage',
  'bias',
  'contradiction',
];

export function JudgeProfileEditor({ profileId, onClose, onSave }: JudgeProfileEditorProps) {
  const [profile, setProfile] = useState<JudgeProfileConfig | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadProfile();
  }, [profileId]);

  const loadProfile = async () => {
    try {
      setLoading(true);
      const response = await apiClient.getJudgeProfile(profileId);
      setProfile(response.profile);
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Failed to load judge profile');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    if (!profile) return;

    try {
      setSaving(true);
      await apiClient.updateJudgeProfile(profileId, profile);
      onSave();
    } catch (err: any) {
      setError(err.message || 'Failed to save judge profile');
    } finally {
      setSaving(false);
    }
  };

  const updateCheck = (checkKey: keyof Omit<JudgeProfileConfig, 'description'>, field: keyof CheckConfig, value: any) => {
    if (!profile) return;
    setProfile({
      ...profile,
      [checkKey]: {
        ...profile[checkKey],
        [field]: value,
      },
    });
  };

  if (loading) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-6">
          <p className="text-gray-600">Loading judge profile...</p>
        </div>
      </div>
    );
  }

  if (!profile) {
    return null;
  }

  const renderCheckEditor = (checkKey: keyof Omit<JudgeProfileConfig, 'description'>) => {
    const check = profile[checkKey];
    const isInvertedScore = ['hallucination', 'toxicity', 'pii_leakage', 'bias', 'contradiction'].includes(checkKey);

    return (
      <div key={checkKey} className="border border-gray-200 rounded-md p-4">
        <div className="flex items-start justify-between mb-3">
          <div className="flex-1">
            <div className="flex items-center">
              <label className="flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={check.enabled}
                  onChange={(e) => updateCheck(checkKey, 'enabled', e.target.checked)}
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
                <span className="ml-2 text-sm font-medium text-black">
                  {CHECK_LABELS[checkKey]}
                </span>
              </label>
              <Tooltip content={CHECK_TOOLTIPS[checkKey]}>
                <span className="ml-2 text-gray-400">ⓘ</span>
              </Tooltip>
            </div>
            <p className="text-xs text-gray-600 mt-1">{check.description}</p>
          </div>
        </div>

        {check.enabled && (
          <div className="space-y-3 mt-3 pt-3 border-t border-gray-200">
            <div className="grid grid-cols-2 gap-3">
              {/* Threshold */}
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">
                  Threshold {isInvertedScore && '(lower = stricter)'}
                </label>
                <input
                  type="number"
                  value={check.threshold}
                  onChange={(e) => updateCheck(checkKey, 'threshold', parseFloat(e.target.value) || 0)}
                  min="0"
                  max="1"
                  step="0.05"
                  className="w-full px-2 py-1 text-sm border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 text-black"
                />
              </div>

              {/* Hard Fail */}
              <div className="flex items-center">
                <label className="flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    checked={check.hard_fail}
                    onChange={(e) => updateCheck(checkKey, 'hard_fail', e.target.checked)}
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                  <div className="ml-2">
                    <span className="text-xs font-medium text-black">Hard Fail</span>
                    <p className="text-xs text-gray-600">Reject answer if check fails</p>
                  </div>
                </label>
              </div>
            </div>
          </div>
        )}
      </div>
    );
  };

  const enabledChecks = CHECK_KEYS.filter((key) => profile[key].enabled).length;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4 overflow-y-auto">
      <div className="bg-white rounded-lg shadow-xl max-w-5xl w-full my-8">
        {/* Header */}
        <div className="border-b border-gray-200 px-6 py-4 flex justify-between items-center">
          <div>
            <h2 className="text-xl font-semibold text-black">Edit Judge Profile</h2>
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
              Profile Description
            </label>
            <input
              type="text"
              value={profile.description}
              onChange={(e) => setProfile({ ...profile, description: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 text-black"
            />
          </div>

          {/* Quality Checks Section */}
          <div className="border-t border-gray-200 pt-4">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-md font-semibold text-black">Quality Checks</h3>
              <span className="text-xs text-gray-600">
                {enabledChecks} of {CHECK_KEYS.length} checks enabled
              </span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Citation & Groundedness Checks */}
              <div className="space-y-4">
                <h4 className="text-sm font-semibold text-gray-700">Accuracy Checks</h4>
                {renderCheckEditor('citation_coverage')}
                {renderCheckEditor('groundedness')}
                {renderCheckEditor('hallucination')}
              </div>

              {/* Relevance & Consistency Checks */}
              <div className="space-y-4">
                <h4 className="text-sm font-semibold text-gray-700">Quality Checks</h4>
                {renderCheckEditor('relevance')}
                {renderCheckEditor('consistency')}
                {renderCheckEditor('contradiction')}
              </div>

              {/* Safety Checks */}
              <div className="space-y-4 md:col-span-2">
                <h4 className="text-sm font-semibold text-gray-700">Safety & Compliance Checks</h4>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {renderCheckEditor('toxicity')}
                  {renderCheckEditor('pii_leakage')}
                  {renderCheckEditor('bias')}
                </div>
              </div>
            </div>
          </div>

          {/* Configuration Preview */}
          <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
            <h3 className="text-sm font-semibold text-blue-900 mb-2">Configuration Summary</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-xs">
              <div>
                <span className="text-blue-700">Enabled:</span> <span className="font-mono text-black">{enabledChecks}/9</span>
              </div>
              <div>
                <span className="text-blue-700">Hard Fails:</span> <span className="font-mono text-black">
                  {CHECK_KEYS.filter((key) => profile[key].enabled && profile[key].hard_fail).length}
                </span>
              </div>
              <div>
                <span className="text-blue-700">Soft Warnings:</span> <span className="font-mono text-black">
                  {CHECK_KEYS.filter((key) => profile[key].enabled && !profile[key].hard_fail).length}
                </span>
              </div>
              <div>
                <span className="text-blue-700">Disabled:</span> <span className="font-mono text-black">
                  {CHECK_KEYS.filter((key) => !profile[key].enabled).length}
                </span>
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
