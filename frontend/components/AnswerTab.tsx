/**
 * Answer Tab - View generated answer with citations
 */

import { Answer, JudgeReport } from '@/lib/types';

interface AnswerTabProps {
  answer: Answer | null;
  judgeReport?: JudgeReport | null;
}

export function AnswerTab({ answer, judgeReport }: AnswerTabProps) {
  if (!answer) {
    return (
      <div className="text-center py-12 text-gray-500">
        <p>No answer yet. Execute a query to see the generated answer.</p>
      </div>
    );
  }

  const confidenceColors = {
    high: 'bg-green-100 text-green-800',
    medium: 'bg-yellow-100 text-yellow-800',
    low: 'bg-red-100 text-red-800',
  };
  const answerText = (answer as any).answer_text ?? (answer as any).answer ?? '';
  const citations = (answer as any).citations ?? [];
  const assumptions = Array.isArray((answer as any).assumptions) ? (answer as any).assumptions : [];
  const limitations = Array.isArray((answer as any).limitations) ? (answer as any).limitations : [];
  const confidence = (answer as any).confidence ?? 'low';
  const isBlocked = judgeReport?.decision === 'FAIL_BLOCKED';

  return (
    <div className="space-y-6">
      <div>
        <div className="flex items-center justify-between mb-2">
          <h2 className="text-lg font-semibold text-gray-900">Generated Answer</h2>
          <span className={`px-3 py-1 rounded-full text-sm font-medium ${confidenceColors[confidence]}`}>
            {confidence.charAt(0).toUpperCase() + confidence.slice(1)} Confidence
          </span>
        </div>
        <p className="text-sm text-gray-600">
          LLM-generated answer with citations and metadata
        </p>
      </div>

      {isBlocked && (
        <div className="border border-red-200 bg-red-50 rounded-lg px-4 py-3 text-sm text-red-800">
          This answer was blocked by the judge. Review the Judge tab for violations and use with caution.
        </div>
      )}

      {/* Answer Text */}
      <div className="border border-gray-200 rounded-lg">
        <div className="bg-gray-50 px-4 py-3 border-b border-gray-200">
          <h3 className="text-sm font-semibold text-gray-900">Answer</h3>
        </div>
        <div className="p-6">
          <p className="text-base text-gray-900 leading-relaxed whitespace-pre-wrap">
            {answerText}
          </p>
        </div>
      </div>

      {/* Citations */}
      <div className="border border-gray-200 rounded-lg">
        <div className="bg-gray-50 px-4 py-3 border-b border-gray-200 flex justify-between items-center">
          <h3 className="text-sm font-semibold text-gray-900">
            Citations ({citations.length})
          </h3>
          <span className="text-xs text-gray-500">Sources for this answer</span>
        </div>
        <div className="divide-y divide-gray-200">
          {citations.map((citation: any, idx: number) => (
            <div key={citation.chunk_id} className="p-4 hover:bg-gray-50">
              <div className="flex items-start gap-3">
                <span className="flex items-center justify-center w-6 h-6 bg-blue-600 text-white text-xs font-bold rounded flex-shrink-0">
                  {idx + 1}
                </span>
                <div className="flex-1">
                  <p className="text-sm text-gray-800 mb-2">
                    {citation.text ?? citation.quote ?? ''}
                  </p>
                  <div className="flex flex-wrap gap-2 text-xs text-gray-500">
                    <span>Doc: {citation.doc_id}</span>
                    <span>•</span>
                    <span>Page: {citation.page_number ?? citation.page_no}</span>
                    <span>•</span>
                    <span className="font-mono">{citation.chunk_id}</span>
                    {citation.score !== undefined && (
                      <>
                        <span>•</span>
                        <span>Score: {citation.score.toFixed(3)}</span>
                      </>
                    )}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Assumptions */}
      {assumptions.length > 0 && (
        <div className="border border-yellow-200 bg-yellow-50 rounded-lg">
          <div className="px-4 py-3 border-b border-yellow-200">
            <h3 className="text-sm font-semibold text-yellow-900">
              Assumptions ({assumptions.length})
            </h3>
          </div>
          <div className="p-4">
            <ul className="space-y-2">
              {assumptions.map((assumption: string, idx: number) => (
                <li key={idx} className="flex items-start gap-2 text-sm text-yellow-900">
                  <span className="text-yellow-600 mt-0.5">⚠</span>
                  <span>{assumption}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}

      {/* Limitations */}
      {limitations.length > 0 && (
        <div className="border border-orange-200 bg-orange-50 rounded-lg">
          <div className="px-4 py-3 border-b border-orange-200">
            <h3 className="text-sm font-semibold text-orange-900">
              Limitations ({limitations.length})
            </h3>
          </div>
          <div className="p-4">
            <ul className="space-y-2">
              {limitations.map((limitation: string, idx: number) => (
                <li key={idx} className="flex items-start gap-2 text-sm text-orange-900">
                  <span className="text-orange-600 mt-0.5">ℹ</span>
                  <span>{limitation}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}
    </div>
  );
}
