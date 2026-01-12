/**
 * Retrieval Tab - View tri-modal retrieval results
 */

import { RetrievalBundle } from '@/lib/types';

interface RetrievalTabProps {
  retrievalBundle: RetrievalBundle | null;
}

export function RetrievalTab({ retrievalBundle }: RetrievalTabProps) {
  if (!retrievalBundle) {
    return (
      <div className="text-center py-12 text-gray-500">
        <p>No retrieval results yet. Execute a query to see retrieval data.</p>
      </div>
    );
  }

  const { vector_results, document_results, graph_results } = retrievalBundle;

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold text-gray-900 mb-2">Tri-Modal Retrieval Results</h2>
        <p className="text-sm text-gray-600">
          Results from vector, document, and graph retrieval modalities
        </p>
      </div>

      {/* Vector Results */}
      <div className="border border-gray-200 rounded-lg overflow-hidden">
        <div className="bg-blue-50 px-4 py-3 border-b border-gray-200">
          <h3 className="text-sm font-semibold text-gray-900">
            Vector Retrieval ({vector_results?.length || 0} results)
          </h3>
          <p className="text-xs text-gray-600">Semantic similarity via embeddings</p>
        </div>
        <div className="divide-y divide-gray-200 max-h-96 overflow-y-auto">
          {vector_results?.map((result, idx) => (
            <div key={result.chunk_id} className="p-4 hover:bg-gray-50">
              <div className="flex justify-between items-start mb-2">
                <span className="text-xs font-mono text-gray-500">#{idx + 1}</span>
                <span className="px-2 py-1 bg-blue-100 text-blue-800 text-xs font-medium rounded">
                  Score: {result.score.toFixed(3)}
                </span>
              </div>
              <p className="text-sm text-gray-800 mb-2">{result.text}</p>
              <div className="flex gap-2 text-xs text-gray-500">
                <span>Doc: {result.metadata?.doc_id}</span>
                <span>•</span>
                <span>Page: {result.metadata?.page_number}</span>
                <span>•</span>
                <span className="font-mono">{result.chunk_id}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Document Results */}
      <div className="border border-gray-200 rounded-lg overflow-hidden">
        <div className="bg-green-50 px-4 py-3 border-b border-gray-200">
          <h3 className="text-sm font-semibold text-gray-900">
            Document Retrieval ({document_results?.length || 0} results)
          </h3>
          <p className="text-xs text-gray-600">BM25 + TF-IDF keyword matching</p>
        </div>
        <div className="divide-y divide-gray-200 max-h-96 overflow-y-auto">
          {document_results?.map((result, idx) => (
            <div key={result.chunk_id} className="p-4 hover:bg-gray-50">
              <div className="flex justify-between items-start mb-2">
                <span className="text-xs font-mono text-gray-500">#{idx + 1}</span>
                <span className="px-2 py-1 bg-green-100 text-green-800 text-xs font-medium rounded">
                  Score: {result.score.toFixed(3)}
                </span>
              </div>
              <p className="text-sm text-gray-800 mb-2">{result.text}</p>
              <div className="flex gap-2 text-xs text-gray-500">
                <span>Doc: {result.metadata?.doc_id}</span>
                <span>•</span>
                <span>Page: {result.metadata?.page_number}</span>
                <span>•</span>
                <span className="font-mono">{result.chunk_id}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Graph Results */}
      <div className="border border-gray-200 rounded-lg overflow-hidden">
        <div className="bg-purple-50 px-4 py-3 border-b border-gray-200">
          <h3 className="text-sm font-semibold text-gray-900">
            Graph Retrieval ({graph_results?.length || 0} results)
          </h3>
          <p className="text-xs text-gray-600">Entity linking and subgraph extraction</p>
        </div>
        <div className="divide-y divide-gray-200 max-h-96 overflow-y-auto">
          {graph_results?.map((result, idx) => (
            <div key={result.chunk_id} className="p-4 hover:bg-gray-50">
              <div className="flex justify-between items-start mb-2">
                <span className="text-xs font-mono text-gray-500">#{idx + 1}</span>
                <span className="px-2 py-1 bg-purple-100 text-purple-800 text-xs font-medium rounded">
                  Score: {result.score.toFixed(3)}
                </span>
              </div>
              {result.entities && result.entities.length > 0 && (
                <div className="flex flex-wrap gap-1 mb-2">
                  {result.entities.map((entity) => (
                    <span
                      key={entity}
                      className="px-2 py-0.5 bg-purple-100 text-purple-700 text-xs rounded"
                    >
                      {entity}
                    </span>
                  ))}
                </div>
              )}
              <p className="text-sm text-gray-800 mb-2">{result.text}</p>
              <div className="flex gap-2 text-xs text-gray-500">
                <span>Doc: {result.metadata?.doc_id}</span>
                <span>•</span>
                <span>Page: {result.metadata?.page_number}</span>
                <span>•</span>
                <span className="font-mono">{result.chunk_id}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
