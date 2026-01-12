/**
 * Context Tab - View compiled context pack
 */

import { ContextPack } from '@/lib/types';

interface ContextTabProps {
  contextPack: ContextPack | null;
}

export function ContextTab({ contextPack }: ContextTabProps) {
  if (!contextPack) {
    return (
      <div className="text-center py-12 text-gray-500">
        <p>No context pack yet. Execute a query to see compiled context.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold text-gray-900 mb-2">Context Pack</h2>
        <p className="text-sm text-gray-600">
          Compiled context within token budget with PII redaction
        </p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-blue-50 rounded-lg p-4">
          <div className="text-2xl font-bold text-blue-900">{contextPack.tokens_used || 0}</div>
          <div className="text-sm text-blue-700">Tokens Used</div>
        </div>
        <div className="bg-green-50 rounded-lg p-4">
          <div className="text-2xl font-bold text-green-900">{contextPack.chunks?.length || 0}</div>
          <div className="text-sm text-green-700">Chunks Included</div>
        </div>
        <div className="bg-purple-50 rounded-lg p-4">
          <div className="text-2xl font-bold text-purple-900">
            {Object.keys(contextPack.coverage || {}).length}
          </div>
          <div className="text-sm text-purple-700">Query Terms Covered</div>
        </div>
      </div>

      {/* Context Text */}
      <div className="border border-gray-200 rounded-lg">
        <div className="bg-gray-50 px-4 py-3 border-b border-gray-200">
          <h3 className="text-sm font-semibold text-gray-900">Context Text</h3>
        </div>
        <div className="p-4 max-h-96 overflow-y-auto">
          <pre className="whitespace-pre-wrap text-sm text-gray-800 font-mono leading-relaxed">
            {contextPack.context_text}
          </pre>
        </div>
      </div>

      {/* Chunks Included */}
      {contextPack.chunks && contextPack.chunks.length > 0 && (
        <div className="border border-gray-200 rounded-lg">
          <div className="bg-gray-50 px-4 py-3 border-b border-gray-200">
            <h3 className="text-sm font-semibold text-gray-900">Included Chunks</h3>
          </div>
          <div className="p-4">
            <div className="space-y-3">
              {contextPack.chunks.map((chunk) => (
                <div
                  key={chunk.chunk_id}
                  className="p-3 bg-gray-50 rounded border border-gray-200"
                >
                  <div className="flex justify-between items-start mb-2">
                    <span className="text-xs font-mono text-gray-600">{chunk.chunk_id}</span>
                    <span className="text-xs text-gray-500">Rank: {chunk.rank}</span>
                  </div>
                  <div className="flex gap-2 text-xs text-gray-600">
                    <span>Doc: {chunk.doc_id}</span>
                    <span>•</span>
                    <span>Page: {chunk.page_no}</span>
                    <span>•</span>
                    <span>Tokens: {chunk.tokens}</span>
                    <span>•</span>
                    <span>Score: {chunk.rrf_score.toFixed(4)}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Query Coverage */}
      {contextPack.coverage && Object.keys(contextPack.coverage).length > 0 && (
        <div className="border border-gray-200 rounded-lg">
          <div className="bg-gray-50 px-4 py-3 border-b border-gray-200">
            <h3 className="text-sm font-semibold text-gray-900">Query Coverage</h3>
            <p className="text-xs text-gray-500 mt-1">Query terms matched in context chunks</p>
          </div>
          <div className="divide-y divide-gray-200">
            {Object.entries(contextPack.coverage).map(([term, chunkIds]: [string, string[]]) => (
              <div key={term} className="p-4">
                <div className="flex justify-between items-start mb-2">
                  <span className="text-sm font-medium text-gray-900">{term}</span>
                  <span className="text-xs text-gray-500">
                    {chunkIds.length} chunk{chunkIds.length !== 1 ? 's' : ''}
                  </span>
                </div>
                <div className="flex flex-wrap gap-1">
                  {chunkIds.map((chunkId) => (
                    <span
                      key={chunkId}
                      className="px-2 py-1 bg-blue-50 text-blue-700 text-xs font-mono rounded"
                    >
                      {chunkId.substring(0, 12)}...
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Redactions Applied */}
      {contextPack.redactions_applied && contextPack.redactions_applied.length > 0 && (
        <div className="border border-yellow-200 bg-yellow-50 rounded-lg p-4">
          <h3 className="text-sm font-semibold text-yellow-900 mb-2">PII Redactions Applied</h3>
          <div className="flex flex-wrap gap-2">
            {contextPack.redactions_applied.map((redaction, idx) => (
              <span
                key={idx}
                className="px-2 py-1 bg-yellow-100 text-yellow-800 text-xs font-medium rounded"
              >
                {redaction}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
