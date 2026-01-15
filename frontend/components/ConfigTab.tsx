/**
 * Config Tab - View configuration profiles and settings
 */

import { useState, useEffect } from 'react';
import { apiClient } from '@/lib/api';
import { WorkflowEditor } from './WorkflowEditor';
import { ProfileDetailsModal } from './ProfileDetailsModal';
import { ChunkingProfileEditor } from './ChunkingProfileEditor';
import { RetrievalProfileEditor } from './RetrievalProfileEditor';
import { FusionProfileEditor } from './FusionProfileEditor';
import { RerankProfileEditor } from './RerankProfileEditor';
import { ContextProfileEditor } from './ContextProfileEditor';
import { JudgeProfileEditor } from './JudgeProfileEditor';
import { ChatProfileEditor } from './ChatProfileEditor';

export function ConfigTab() {
  const [profiles, setProfiles] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeSection, setActiveSection] = useState<string>('workflows');
  const [editingWorkflow, setEditingWorkflow] = useState<string | null>(null);
  const [editingChunkingProfile, setEditingChunkingProfile] = useState<string | null>(null);
  const [editingRetrievalProfile, setEditingRetrievalProfile] = useState<string | null>(null);
  const [editingFusionProfile, setEditingFusionProfile] = useState<string | null>(null);
  const [editingRerankProfile, setEditingRerankProfile] = useState<string | null>(null);
  const [editingContextProfile, setEditingContextProfile] = useState<string | null>(null);
  const [editingJudgeProfile, setEditingJudgeProfile] = useState<string | null>(null);
  const [editingChatProfile, setEditingChatProfile] = useState<string | null>(null);
  const [viewingProfile, setViewingProfile] = useState<{ id: string; type: string } | null>(null);
  const [promptData, setPromptData] = useState<any>(null);
  const [promptLoading, setPromptLoading] = useState(false);
  const [promptSaving, setPromptSaving] = useState(false);
  const [generationSettings, setGenerationSettings] = useState({
    model: 'gpt-3.5-turbo',
    temperature: 0.0,
    top_p: 1.0,
    max_tokens: 2000,
  });

  useEffect(() => {
    loadProfiles();
  }, []);

  useEffect(() => {
    if (activeSection === 'generation') {
      loadPrompts();
    }
  }, [activeSection]);

  const loadProfiles = async () => {
    try {
      setLoading(true);
      const data = await apiClient.listAllProfiles();
      setProfiles(data.profiles);
      setError(null);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const loadPrompts = async () => {
    try {
      setPromptLoading(true);
      const data = await apiClient.getPrompts();
      setPromptData(data.prompts);
      setError(null);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setPromptLoading(false);
    }
  };

  const handlePromptSave = async () => {
    try {
      setPromptSaving(true);
      const updated = await apiClient.updatePrompts(promptData);
      setPromptData(updated.prompts);
      alert('Prompt configuration saved successfully');
    } catch (err: any) {
      alert(`Failed to save prompts: ${err.message}`);
    } finally {
      setPromptSaving(false);
    }
  };

  const handleReload = async () => {
    try {
      await apiClient.reloadConfig();
      await loadProfiles();
      if (activeSection === 'generation') {
        await loadPrompts();
      }
      alert('Configuration reloaded successfully');
    } catch (err: any) {
      alert(`Failed to reload configuration: ${err.message}`);
    }
  };

  const handleWorkflowSaved = async () => {
    setEditingWorkflow(null);
    await loadProfiles();
    alert('Workflow saved successfully');
  };

  const handleChunkingProfileSaved = async () => {
    setEditingChunkingProfile(null);
    await loadProfiles();
    alert('Chunking profile saved successfully');
  };

  const handleRetrievalProfileSaved = async () => {
    setEditingRetrievalProfile(null);
    await loadProfiles();
    alert('Retrieval profile saved successfully');
  };

  const handleFusionProfileSaved = async () => {
    setEditingFusionProfile(null);
    await loadProfiles();
    alert('Fusion profile saved successfully');
  };

  const handleRerankProfileSaved = async () => {
    setEditingRerankProfile(null);
    await loadProfiles();
    alert('Reranking profile saved successfully');
  };

  const handleContextProfileSaved = async () => {
    setEditingContextProfile(null);
    await loadProfiles();
    alert('Context profile saved successfully');
  };

  const handleJudgeProfileSaved = async () => {
    setEditingJudgeProfile(null);
    await loadProfiles();
    alert('Judge profile saved successfully');
  };

  const handleChatProfileSaved = async () => {
    setEditingChatProfile(null);
    await loadProfiles();
    alert('Chat profile saved successfully');
  };

  if (loading) {
    return (
      <div className="text-center py-12 text-gray-500">
        <p>Loading configuration...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <p className="text-red-600 mb-4">Error loading configuration: {error}</p>
        <button
          onClick={loadProfiles}
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
          title="Retry loading configuration profiles from the server"
        >
          Retry
        </button>
      </div>
    );
  }

  const sections = [
    { id: 'workflows', label: 'Workflows', count: profiles?.workflows?.length || 0 },
    { id: 'chunking', label: 'Chunking', count: profiles?.chunking?.length || 0 },
    { id: 'graph_extraction', label: 'Graph Extraction', count: profiles?.graph_extraction?.length || 0 },
    { id: 'retrieval', label: 'Retrieval', count: profiles?.retrieval?.length || 0 },
    { id: 'fusion', label: 'Fusion', count: profiles?.fusion?.length || 0 },
    { id: 'reranking', label: 'Reranking', count: profiles?.reranking?.length || 0 },
    { id: 'context', label: 'Context', count: profiles?.context?.length || 0 },
    { id: 'generation', label: 'Generation', count: profiles?.prompts?.length || 0 },
    { id: 'judge', label: 'Judge', count: profiles?.judge?.length || 0 },
    { id: 'chat', label: 'Chat', count: profiles?.chat?.length || 0 },
  ];

  const updateGenerationPrompt = (value: string) => {
    setPromptData((prev: any) => ({
      ...(prev || {}),
      generation: {
        ...((prev || {}).generation || {}),
        system_prompt: value,
      },
    }));
  };

  const renderGenerationSection = () => {
    if (promptLoading) {
      return (
        <div className="text-center py-12 text-gray-500">
          <p>Loading generation settings...</p>
        </div>
      );
    }

    if (!promptData) {
      return (
        <div className="text-center py-12 text-gray-500">
          <p>No generation configuration loaded.</p>
        </div>
      );
    }

    const generationPrompt = promptData?.generation?.system_prompt || '';

    return (
      <div className="border border-gray-200 rounded-lg p-4 bg-white space-y-3">
        <div>
          <h3 className="text-sm font-semibold text-black">Generation Settings</h3>
          <p className="text-xs text-gray-600">
            Prompt changes apply after saving and reloading config. Other settings are UI-only for now.
          </p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">LLM Model</label>
            <input
              type="text"
              value={generationSettings.model}
              onChange={(e) => setGenerationSettings({ ...generationSettings, model: e.target.value })}
              className="w-full text-sm text-gray-900 border border-gray-300 rounded-md px-3 py-2"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">Max Tokens</label>
            <input
              type="number"
              min="1"
              value={generationSettings.max_tokens}
              onChange={(e) => setGenerationSettings({ ...generationSettings, max_tokens: parseInt(e.target.value) || 0 })}
              className="w-full text-sm text-gray-900 border border-gray-300 rounded-md px-3 py-2"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">Temperature</label>
            <input
              type="number"
              min="0"
              max="1"
              step="0.1"
              value={generationSettings.temperature}
              onChange={(e) => setGenerationSettings({ ...generationSettings, temperature: parseFloat(e.target.value) || 0 })}
              className="w-full text-sm text-gray-900 border border-gray-300 rounded-md px-3 py-2"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">Top P</label>
            <input
              type="number"
              min="0"
              max="1"
              step="0.1"
              value={generationSettings.top_p}
              onChange={(e) => setGenerationSettings({ ...generationSettings, top_p: parseFloat(e.target.value) || 0 })}
              className="w-full text-sm text-gray-900 border border-gray-300 rounded-md px-3 py-2"
            />
          </div>
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-700 mb-1">System Prompt</label>
          <textarea
            value={generationPrompt}
            onChange={(e) => updateGenerationPrompt(e.target.value)}
            rows={12}
            className="w-full text-sm text-gray-900 border border-gray-300 rounded-md p-3 font-mono"
          />
        </div>
        <div className="flex justify-end gap-2">
          <button
            onClick={() => alert('Generation settings are UI-only for now.')}
            className="px-4 py-2 text-sm border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50"
          >
            Save Settings
          </button>
          <button
            onClick={handlePromptSave}
            disabled={promptSaving}
            className="px-4 py-2 text-sm bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
          >
            {promptSaving ? 'Saving...' : 'Save Prompt'}
          </button>
        </div>
      </div>
    );
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-lg font-semibold text-black">Configuration Profiles</h2>
          <p className="text-sm text-gray-900">
            View and manage all configuration profiles
          </p>
        </div>
        <button
          onClick={handleReload}
          className="px-4 py-2 bg-blue-600 text-white text-sm rounded-md hover:bg-blue-700"
          title="Reload all configuration profiles from JSON files without restarting the server"
        >
          Reload Config
        </button>
      </div>

      {/* Section Navigation */}
      <div className="flex gap-2 overflow-x-auto pb-2">
        {sections.map((section) => (
          <button
            key={section.id}
            onClick={() => setActiveSection(section.id)}
            className={`px-4 py-2 text-sm font-medium rounded-md whitespace-nowrap ${
              activeSection === section.id
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 text-black hover:bg-gray-200'
            }`}
          >
            {section.label} ({section.count})
          </button>
        ))}
      </div>

      {/* Profile List */}
      {activeSection === 'generation' ? (
        renderGenerationSection()
      ) : (
        <div className="border border-gray-200 rounded-lg divide-y divide-gray-200">
          {profiles && profiles[activeSection]?.map((profileId: string) => (
            <div key={profileId} className="p-4 hover:bg-gray-50">
              <div className="flex justify-between items-center">
                <div>
                  <div className="font-medium text-black">{profileId}</div>
                  <div className="text-xs text-gray-900 font-mono">{activeSection} profile</div>
                </div>
                <button
                  onClick={() => {
                    if (activeSection === 'workflows') {
                      setEditingWorkflow(profileId);
                    } else if (activeSection === 'chunking') {
                      setEditingChunkingProfile(profileId);
                    } else if (activeSection === 'retrieval') {
                      setEditingRetrievalProfile(profileId);
                    } else if (activeSection === 'fusion') {
                      setEditingFusionProfile(profileId);
                    } else if (activeSection === 'reranking') {
                      setEditingRerankProfile(profileId);
                    } else if (activeSection === 'context') {
                      setEditingContextProfile(profileId);
                    } else if (activeSection === 'judge') {
                      setEditingJudgeProfile(profileId);
                    } else if (activeSection === 'chat') {
                      setEditingChatProfile(profileId);
                    } else {
                      setViewingProfile({ id: profileId, type: activeSection });
                    }
                  }}
                  className="px-3 py-1 text-xs bg-gray-100 text-black rounded hover:bg-gray-200"
                  title={['workflows', 'chunking', 'retrieval', 'fusion', 'reranking', 'context', 'judge', 'chat'].includes(activeSection) ? 'Edit configuration with detailed field explanations' : 'View detailed configuration settings for this profile'}
                >
                  {['workflows', 'chunking', 'retrieval', 'fusion', 'reranking', 'context', 'judge', 'chat'].includes(activeSection) ? 'Edit' : 'View Details'}
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Stats Summary */}
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-blue-50 rounded-lg p-4">
          <div className="text-2xl font-bold text-black">{profiles?.workflows?.length || 0}</div>
          <div className="text-sm text-gray-900">Workflow Profiles</div>
        </div>
        <div className="bg-green-50 rounded-lg p-4">
          <div className="text-2xl font-bold text-black">{profiles?.retrieval?.length || 0}</div>
          <div className="text-sm text-gray-900">Retrieval Profiles</div>
        </div>
        <div className="bg-purple-50 rounded-lg p-4">
          <div className="text-2xl font-bold text-black">{profiles?.judge?.length || 0}</div>
          <div className="text-sm text-gray-900">Judge Profiles</div>
        </div>
      </div>

      {/* Workflow Editor Modal */}
      {editingWorkflow && (
        <WorkflowEditor
          workflowId={editingWorkflow}
          onClose={() => setEditingWorkflow(null)}
          onSave={handleWorkflowSaved}
        />
      )}

      {/* Chunking Profile Editor Modal */}
      {editingChunkingProfile && (
        <ChunkingProfileEditor
          profileId={editingChunkingProfile}
          onClose={() => setEditingChunkingProfile(null)}
          onSave={handleChunkingProfileSaved}
        />
      )}

      {/* Retrieval Profile Editor Modal */}
      {editingRetrievalProfile && (
        <RetrievalProfileEditor
          profileId={editingRetrievalProfile}
          onClose={() => setEditingRetrievalProfile(null)}
          onSave={handleRetrievalProfileSaved}
        />
      )}

      {/* Fusion Profile Editor Modal */}
      {editingFusionProfile && (
        <FusionProfileEditor
          profileId={editingFusionProfile}
          onClose={() => setEditingFusionProfile(null)}
          onSave={handleFusionProfileSaved}
        />
      )}

      {/* Reranking Profile Editor Modal */}
      {editingRerankProfile && (
        <RerankProfileEditor
          profileId={editingRerankProfile}
          onClose={() => setEditingRerankProfile(null)}
          onSave={handleRerankProfileSaved}
        />
      )}

      {/* Context Profile Editor Modal */}
      {editingContextProfile && (
        <ContextProfileEditor
          profileId={editingContextProfile}
          onClose={() => setEditingContextProfile(null)}
          onSave={handleContextProfileSaved}
        />
      )}

      {/* Judge Profile Editor Modal */}
      {editingJudgeProfile && (
        <JudgeProfileEditor
          profileId={editingJudgeProfile}
          onClose={() => setEditingJudgeProfile(null)}
          onSave={handleJudgeProfileSaved}
        />
      )}

      {/* Chat Profile Editor Modal */}
      {editingChatProfile && (
        <ChatProfileEditor
          profileId={editingChatProfile}
          onClose={() => setEditingChatProfile(null)}
          onSave={handleChatProfileSaved}
        />
      )}

      {/* Profile Details Modal */}
      {viewingProfile && (
        <ProfileDetailsModal
          profileId={viewingProfile.id}
          profileType={viewingProfile.type}
          onClose={() => setViewingProfile(null)}
          onSave={async () => {
            setViewingProfile(null);
            await loadProfiles();
          }}
        />
      )}
    </div>
  );
}
