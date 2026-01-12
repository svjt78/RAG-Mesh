/**
 * Fusion Tab - View fused and reranked results
 */

import { FusedResult } from '@/lib/types';

interface FusionTabProps {
  fusedResults: FusedResult[] | null;
}

export function FusionTab({ fusedResults }: FusionTabProps) {
  if (!fusedResults || fusedResults.length === 0) {
    return (
      <div className="text-center py-12 text-gray-500">
        <p>No fusion results yet. Execute a query to see fused results.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold text-gray-900 mb-2">
          Fused Results ({fusedResults.length})
        </h2>
        <p className="text-sm text-gray-600">
          Weighted Reciprocal Rank Fusion (RRF) of all three modalities
        </p>
      </div>

      <div className="border border-gray-200 rounded-lg divide-y divide-gray-200">
        {fusedResults.map((result, idx) => {
          // Handle both old and new backend response formats
          const rawResult = result as any;
          const finalScore = rawResult.final_score ?? rawResult.rrf_score ?? 0;
          const vectorScore = rawResult.sources?.vector ?? rawResult.vector_score;
          const documentScore = rawResult.sources?.document ?? rawResult.document_score;
          const graphScore = rawResult.sources?.graph ?? rawResult.graph_score;
          const chunkText = rawResult.text ?? rawResult.metadata?.text;

          return (
            <div key={result.chunk_id} className="p-4 hover:bg-gray-50">
              <div className="flex justify-between items-start mb-3">
                <div className="flex items-center gap-3">
                  <span className="flex items-center justify-center w-8 h-8 bg-gray-900 text-white text-sm font-bold rounded">
                    {idx + 1}
                  </span>
                  <div>
                    <div className="text-sm font-medium text-gray-900">
                      Final Score: {finalScore.toFixed(4)}
                    </div>
                    <div className="text-xs text-gray-500 font-mono">{result.chunk_id}</div>
                  </div>
                </div>

                {/* Modality Scores */}
                <div className="flex gap-2">
                  {vectorScore !== undefined && vectorScore > 0 && (
                    <span className="px-2 py-1 bg-blue-100 text-blue-800 text-xs font-medium rounded">
                      V: {vectorScore.toFixed(3)}
                    </span>
                  )}
                  {documentScore !== undefined && documentScore > 0 && (
                    <span className="px-2 py-1 bg-green-100 text-green-800 text-xs font-medium rounded">
                      D: {documentScore.toFixed(3)}
                    </span>
                  )}
                  {graphScore !== undefined && graphScore > 0 && (
                    <span className="px-2 py-1 bg-purple-100 text-purple-800 text-xs font-medium rounded">
                      G: {graphScore.toFixed(3)}
                    </span>
                  )}
                </div>
              </div>

              {chunkText && (
                <p className="text-sm text-gray-800 mb-3 leading-relaxed">
                  {chunkText}
                </p>
              )}

              <div className="flex flex-wrap gap-2 text-xs text-gray-500">
                <span>Doc: {result.metadata?.doc_id}</span>
                <span>•</span>
                <span>Page: {result.metadata?.page_number}</span>
                {result.metadata?.doc_type && (
                  <>
                    <span>•</span>
                    <span>Type: {result.metadata.doc_type}</span>
                  </>
                )}
                {result.metadata?.form_number && (
                  <>
                    <span>•</span>
                    <span>Form: {result.metadata.form_number}</span>
                  </>
                )}
              </div>

              {/* Sources Breakdown */}
              <div className="mt-3 pt-3 border-t border-gray-100">
                <div className="text-xs text-gray-600">
                  <span className="font-medium">Sources:</span>
                  {' '}
                  {vectorScore !== undefined && vectorScore > 0 && 'Vector'}
                  {documentScore !== undefined && documentScore > 0 && (vectorScore !== undefined && vectorScore > 0 ? ' + Document' : 'Document')}
                  {graphScore !== undefined && graphScore > 0 && ' + Graph'}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Legend */}
      <div className="bg-gray-50 rounded-lg p-4">
        <h3 className="text-sm font-medium text-gray-900 mb-2">Score Legend</h3>
        <div className="grid grid-cols-3 gap-4 text-xs">
          <div>
            <span className="inline-block px-2 py-1 bg-blue-100 text-blue-800 rounded mb-1">V</span>
            <p className="text-gray-600">Vector (Semantic)</p>
          </div>
          <div>
            <span className="inline-block px-2 py-1 bg-green-100 text-green-800 rounded mb-1">D</span>
            <p className="text-gray-600">Document (Keyword)</p>
          </div>
          <div>
            <span className="inline-block px-2 py-1 bg-purple-100 text-purple-800 rounded mb-1">G</span>
            <p className="text-gray-600">Graph (Entities)</p>
          </div>
        </div>
      </div>
    </div>
  );
}
