/**
 * ProfileDetailsModal - View and edit configuration profile details
 */

import { useState, useEffect } from 'react';
import { apiClient } from '@/lib/api';

interface ProfileDetailsModalProps {
  profileId: string;
  profileType: string;
  onClose: () => void;
  onSave?: () => void;
}

export function ProfileDetailsModal({ profileId, profileType, onClose, onSave }: ProfileDetailsModalProps) {
  const [profileData, setProfileData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [editedData, setEditedData] = useState<any>(null);
  const [isEditing, setIsEditing] = useState(false);

  useEffect(() => {
    loadProfileData();
  }, [profileId, profileType]);

  const loadProfileData = async () => {
    try {
      setLoading(true);
      let data;

      switch (profileType) {
        case 'chunking':
          data = await apiClient.getChunkingProfile(profileId);
          break;
        case 'graph_extraction':
          data = await apiClient.getGraphExtractionProfile(profileId);
          break;
        case 'retrieval':
          data = await apiClient.getRetrievalProfile(profileId);
          break;
        case 'fusion':
          data = await apiClient.getFusionProfile(profileId);
          break;
        case 'context':
          data = await apiClient.getContextProfile(profileId);
          break;
        case 'judge':
          data = await apiClient.getJudgeProfile(profileId);
          break;
        default:
          throw new Error(`Unknown profile type: ${profileType}`);
      }

      const profilePayload = data?.profile ?? data;
      setProfileData(profilePayload);
      setEditedData(JSON.parse(JSON.stringify(profilePayload))); // Deep copy
      setError(null);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (key: string, value: any) => {
    setEditedData((prev: any) => ({
      ...prev,
      [key]: value,
    }));
  };

  const handleSave = async () => {
    try {
      switch (profileType) {
        case 'graph_extraction':
          await apiClient.updateGraphExtractionProfile(profileId, editedData);
          break;
        default:
          throw new Error(`Saving not supported for profile type: ${profileType}`);
      }

      if (onSave) {
        await onSave();
      }
      setIsEditing(false);
    } catch (err: any) {
      alert(`Failed to save profile: ${err.message}`);
    }
  };

  const renderValue = (key: string, value: any): JSX.Element => {
    if (value === null || value === undefined) {
      return <span className="text-gray-400 italic">null</span>;
    }

    if (typeof value === 'boolean') {
      if (isEditing) {
        return (
          <input
            type="checkbox"
            checked={editedData[key]}
            onChange={(e) => handleInputChange(key, e.target.checked)}
            className="h-4 w-4 rounded border-gray-300"
          />
        );
      }
      return <span className={value ? 'text-green-600' : 'text-red-600'}>{value.toString()}</span>;
    }

    if (typeof value === 'number') {
      if (isEditing) {
        return (
          <input
            type="number"
            value={editedData[key]}
            onChange={(e) => handleInputChange(key, parseFloat(e.target.value))}
            className="px-2 py-1 border border-gray-300 rounded w-32"
          />
        );
      }
      return <span className="font-mono">{value}</span>;
    }

    if (typeof value === 'string') {
      if (isEditing) {
        return (
          <input
            type="text"
            value={editedData[key]}
            onChange={(e) => handleInputChange(key, e.target.value)}
            className="px-2 py-1 border border-gray-300 rounded w-full"
          />
        );
      }
      return <span className="font-mono">{value}</span>;
    }

    if (Array.isArray(value)) {
      if (isEditing) {
        return (
          <textarea
            value={Array.isArray(editedData[key]) ? editedData[key].join('\n') : ''}
            onChange={(e) => {
              const nextValue = e.target.value
                .split('\n')
                .map((item) => item.trim())
                .filter((item) => item.length > 0);
              handleInputChange(key, nextValue);
            }}
            rows={Math.min(Math.max(value.length, 3), 10)}
            className="w-full text-sm text-gray-900 border border-gray-300 rounded-md p-2 font-mono"
          />
        );
      }
      return (
        <div className="space-y-1">
          {value.map((item, idx) => (
            <div key={idx} className="text-sm font-mono bg-gray-50 px-2 py-1 rounded">
              {typeof item === 'object' ? JSON.stringify(item) : String(item)}
            </div>
          ))}
        </div>
      );
    }

    if (typeof value === 'object') {
      return (
        <pre className="text-xs bg-gray-50 p-2 rounded overflow-auto max-h-32">
          {JSON.stringify(value, null, 2)}
        </pre>
      );
    }

    return <span>{String(value)}</span>;
  };

  const formatFieldName = (key: string): string => {
    return key
      .split('_')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-3xl w-full max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="flex justify-between items-center p-6 border-b border-gray-200">
          <div>
            <h2 className="text-xl font-semibold text-gray-900">{profileId}</h2>
            <p className="text-sm text-gray-500 mt-1">
              {formatFieldName(profileType)} Profile Configuration
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 text-2xl leading-none"
          >
            ×
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-auto p-6">
          {loading && (
            <div className="text-center py-12 text-gray-500">
              <p>Loading configuration...</p>
            </div>
          )}

          {error && (
            <div className="text-center py-12">
              <p className="text-red-600 mb-4">Error: {error}</p>
              <button
                onClick={loadProfileData}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
              >
                Retry
              </button>
            </div>
          )}

          {profileData && !loading && !error && (
            <div className="space-y-4">
              {Object.entries(isEditing ? editedData : profileData).map(([key, value]) => (
                <div key={key} className="border-b border-gray-100 pb-3">
                  <div className="flex justify-between items-start">
                    <div className="flex-1">
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        {formatFieldName(key)}
                      </label>
                      <div className="text-sm text-gray-900">
                        {renderValue(key, value)}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex justify-between items-center p-6 border-t border-gray-200 bg-gray-50">
          <div className="text-sm text-gray-500">
            {isEditing ? 'Editing mode - modify values above' : 'View-only mode'}
          </div>
          <div className="flex gap-2">
            {isEditing ? (
              <>
                <button
                  onClick={() => {
                    setEditedData(JSON.parse(JSON.stringify(profileData)));
                    setIsEditing(false);
                  }}
                  className="px-4 py-2 text-sm bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300"
                >
                  Cancel
                </button>
                <button
                  onClick={handleSave}
                  className="px-4 py-2 text-sm bg-blue-600 text-white rounded-md hover:bg-blue-700"
                >
                  Save Changes
                </button>
              </>
            ) : (
              <>
                <button
                  onClick={onClose}
                  className="px-4 py-2 text-sm bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300"
                >
                  Close
                </button>
                <button
                  onClick={() => setIsEditing(true)}
                  className="px-4 py-2 text-sm bg-blue-600 text-white rounded-md hover:bg-blue-700"
                >
                  Edit
                </button>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
