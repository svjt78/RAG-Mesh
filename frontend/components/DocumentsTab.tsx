/**
 * Documents Tab - Document management and ingestion
 */

import { useState, useEffect } from 'react';
import { apiClient, Document } from '@/lib/api';

export function DocumentsTab() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [isIndexing, setIsIndexing] = useState(false);
  const [graphExtractionProfiles, setGraphExtractionProfiles] = useState<string[]>([]);
  const [selectedGraphProfile, setSelectedGraphProfile] = useState<string>('generic');

  useEffect(() => {
    loadDocuments();
    loadProfiles();
  }, []);

  const loadProfiles = async () => {
    try {
      const data = await apiClient.listAllProfiles();
      setGraphExtractionProfiles(data.profiles.graph_extraction || []);
    } catch (err: any) {
      console.error('Failed to load graph extraction profiles:', err);
    }
  };

  const loadDocuments = async () => {
    try {
      setLoading(true);
      const data = await apiClient.listDocuments();
      setDocuments(data.documents);
      setError(null);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file && file.type === 'application/pdf') {
      setUploadFile(file);
    } else {
      alert('Please select a PDF file');
    }
  };

  const handleUpload = async () => {
    if (!uploadFile) return;

    try {
      setIsUploading(true);
      const response = await apiClient.ingestPDF(uploadFile);
      alert(`PDF ingested successfully!\nDoc ID: ${response.doc_id}\nPages: ${response.pages}`);

      // Ask if user wants to index now
      if (confirm('Would you like to index this document now?')) {
        await handleIndex(response.doc_id);
      }

      setUploadFile(null);
      await loadDocuments();
    } catch (err: any) {
      alert(`Upload failed: ${err.message}`);
    } finally {
      setIsUploading(false);
    }
  };

  const handleIndex = async (docId: string) => {
    try {
      setIsIndexing(true);
      const response = await apiClient.indexDocument(docId, 'default', selectedGraphProfile);
      alert(
        `Document indexed successfully!\n` +
        `Domain: ${selectedGraphProfile}\n` +
        `Chunks: ${response.chunks_created}\n` +
        `Embeddings: ${response.embeddings_created}\n` +
        `Entities: ${response.entities_extracted}\n` +
        `Relationships: ${response.relationships_extracted}`
      );
      await loadDocuments();
    } catch (err: any) {
      alert(`Indexing failed: ${err.message}`);
    } finally {
      setIsIndexing(false);
    }
  };

  const handleDelete = async (docId: string) => {
    if (!confirm('Are you sure you want to delete this document?')) return;

    try {
      await apiClient.deleteDocument(docId);
      alert('Document deleted successfully');
      await loadDocuments();
    } catch (err: any) {
      alert(`Delete failed: ${err.message}`);
    }
  };

  if (loading) {
    return (
      <div className="text-center py-12 text-gray-500">
        <p>Loading documents...</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold text-gray-900 mb-2">Document Management</h2>
        <p className="text-sm text-gray-600">
          Upload, index, and manage insurance PDF documents
        </p>
      </div>

      {/* Upload Section */}
      <div className="border border-gray-200 rounded-lg p-6 bg-gray-50">
        <h3 className="text-sm font-semibold text-gray-900 mb-4">Upload PDF</h3>

        {/* Domain Selection */}
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Document Domain (Graph Extraction Profile)
          </label>
          <select
            value={selectedGraphProfile}
            onChange={(e) => setSelectedGraphProfile(e.target.value)}
            className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md bg-white text-gray-900"
            title="Select the domain profile for entity and relationship extraction during indexing"
          >
            {graphExtractionProfiles.map((profile) => (
              <option key={profile} value={profile}>
                {profile.charAt(0).toUpperCase() + profile.slice(1)}
                {profile === 'generic' ? ' (Default - All Domains)' : ''}
              </option>
            ))}
          </select>
          <p className="mt-1 text-xs text-gray-500">
            Choose the domain for extracting entities and relationships (e.g., medical, legal, financial)
          </p>
        </div>

        <div className="flex gap-4">
          <input
            type="file"
            accept=".pdf"
            onChange={handleFileSelect}
            className="flex-1 text-sm text-gray-900 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-medium file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
            disabled={isUploading}
            title="Select a PDF file to upload and ingest into the system. The file will be parsed and stored for indexing."
          />
          <button
            onClick={handleUpload}
            disabled={!uploadFile || isUploading}
            className="px-6 py-2 bg-blue-600 text-white text-sm rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            title="Upload the selected PDF file to the system for ingestion"
          >
            {isUploading ? 'Uploading...' : 'Upload'}
          </button>
        </div>
        {uploadFile && (
          <p className="mt-2 text-sm text-gray-600">
            Selected: {uploadFile.name} ({(uploadFile.size / 1024 / 1024).toFixed(2)} MB)
          </p>
        )}
      </div>

      {/* Error Display */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <p className="text-sm text-red-800">{error}</p>
        </div>
      )}

      {/* Documents List */}
      <div>
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-sm font-semibold text-gray-900">
            Documents ({documents.length})
          </h3>
          <button
            onClick={loadDocuments}
            className="px-3 py-1 text-xs bg-gray-100 text-gray-700 rounded hover:bg-gray-200"
            title="Reload the list of documents from the server"
          >
            Refresh
          </button>
        </div>

        {documents.length === 0 ? (
          <div className="text-center py-12 text-gray-500 border border-gray-200 rounded-lg">
            <p>No documents yet. Upload a PDF to get started.</p>
          </div>
        ) : (
          <div className="border border-gray-200 rounded-lg divide-y divide-gray-200">
            {documents.map((doc) => (
              <div key={doc.doc_id} className="p-4 hover:bg-gray-50">
                <div className="flex justify-between items-start mb-2">
                  <div className="flex-1">
                    <div className="font-medium text-gray-900">{doc.filename}</div>
                    <div className="flex flex-wrap gap-2 mt-1 text-xs text-gray-500">
                      <span className="font-mono">{doc.doc_id}</span>
                      <span>•</span>
                      <span>{doc.pages} pages</span>
                      {doc.doc_type && (
                        <>
                          <span>•</span>
                          <span>Type: {doc.doc_type}</span>
                        </>
                      )}
                      {doc.state && (
                        <>
                          <span>•</span>
                          <span>State: {doc.state}</span>
                        </>
                      )}
                      {doc.form_number && (
                        <>
                          <span>•</span>
                          <span>Form: {doc.form_number}</span>
                        </>
                      )}
                    </div>
                  </div>
                  <div className="flex gap-2 ml-4">
                    {doc.indexed_at ? (
                      <span className="px-2 py-1 bg-green-100 text-green-800 text-xs rounded">
                        Indexed
                      </span>
                    ) : (
                      <button
                        onClick={() => handleIndex(doc.doc_id)}
                        disabled={isIndexing}
                        className="px-3 py-1 bg-blue-600 text-white text-xs rounded hover:bg-blue-700 disabled:opacity-50"
                        title="Create chunks, embeddings, and extract entities from this document for retrieval"
                      >
                        {isIndexing ? 'Indexing...' : 'Index'}
                      </button>
                    )}
                    <button
                      onClick={() => handleDelete(doc.doc_id)}
                      className="px-3 py-1 bg-red-100 text-red-700 text-xs rounded hover:bg-red-200"
                      title="Permanently delete this document and all associated chunks, embeddings, and graph data"
                    >
                      Delete
                    </button>
                  </div>
                </div>
                <div className="text-xs text-gray-400">
                  Ingested: {doc.ingested_at ? new Date(doc.ingested_at).toLocaleString() : 'Unknown'}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-blue-50 rounded-lg p-4">
          <div className="text-2xl font-bold text-blue-900">{documents.length}</div>
          <div className="text-sm text-blue-700">Total Documents</div>
        </div>
        <div className="bg-green-50 rounded-lg p-4">
          <div className="text-2xl font-bold text-green-900">
            {documents.filter((d) => d.indexed_at).length}
          </div>
          <div className="text-sm text-green-700">Indexed</div>
        </div>
        <div className="bg-purple-50 rounded-lg p-4">
          <div className="text-2xl font-bold text-purple-900">
            {documents.reduce((sum, d) => sum + d.pages, 0)}
          </div>
          <div className="text-sm text-purple-700">Total Pages</div>
        </div>
      </div>
    </div>
  );
}
