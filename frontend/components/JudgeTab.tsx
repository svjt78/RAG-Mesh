/**
 * Judge Tab - View validation results from all 9 checks
 */

import { JudgeReport } from '@/lib/types';

interface JudgeTabProps {
  judgeReport: JudgeReport | null;
}

export function JudgeTab({ judgeReport }: JudgeTabProps) {
  if (!judgeReport) {
    return (
      <div className="text-center py-12 text-gray-500">
        <p>No judge report yet. Execute a query to see validation results.</p>
      </div>
    );
  }

  const decisionColors = {
    PASS: 'bg-green-100 text-green-800 border-green-200',
    FAIL_BLOCKED: 'bg-red-100 text-red-800 border-red-200',
    FAIL_RETRYABLE: 'bg-yellow-100 text-yellow-800 border-yellow-200',
  };

  return (
    <div className="space-y-6">
      {/* Header with Decision */}
      <div className={`border-2 rounded-lg p-6 ${decisionColors[judgeReport.decision]}`}>
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold mb-2">
              {judgeReport.decision.replace('_', ' ')}
            </h2>
            <p className="text-sm">
              Overall Score: {(judgeReport.overall_score * 100).toFixed(1)}%
            </p>
          </div>
          <div className="text-right">
            <div className="text-sm font-medium">
              {judgeReport.checks.filter((c) => c.status === 'pass').length} / {judgeReport.checks.length} Checks Passed
            </div>
            <div className="text-sm">
              {judgeReport.violations.length} Violations
            </div>
          </div>
        </div>
      </div>

      {/* Violations (if any) */}
      {judgeReport.violations.length > 0 && (
        <div className="border border-red-200 bg-red-50 rounded-lg">
          <div className="px-4 py-3 border-b border-red-200">
            <h3 className="text-sm font-semibold text-red-900">
              Violations ({judgeReport.violations.length})
            </h3>
          </div>
          <div className="divide-y divide-red-200">
            {judgeReport.violations.map((violation, idx) => (
              <div key={idx} className="p-4">
                <div className="flex items-start gap-3">
                  <span className="flex-shrink-0 w-6 h-6 bg-red-600 text-white text-xs font-bold rounded flex items-center justify-center">
                    !
                  </span>
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-medium text-red-900">{violation.check_name}</span>
                      <span className={`px-2 py-0.5 text-xs rounded ${
                        violation.severity === 'hard_fail'
                          ? 'bg-red-600 text-white'
                          : 'bg-yellow-600 text-white'
                      }`}>
                        {violation.severity.replace('_', ' ')}
                      </span>
                    </div>
                    <p className="text-sm text-red-800 mb-2">{violation.message}</p>
                    {violation.details && Object.keys(violation.details).length > 0 && (
                      <pre className="text-xs text-red-700 bg-red-100 p-2 rounded overflow-x-auto">
                        {JSON.stringify(violation.details, null, 2)}
                      </pre>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* All Checks */}
      <div className="border border-gray-200 rounded-lg">
        <div className="bg-gray-50 px-4 py-3 border-b border-gray-200">
          <h3 className="text-sm font-semibold text-gray-900">
            All Checks ({judgeReport.checks.length})
          </h3>
        </div>
        <div className="divide-y divide-gray-200">
          {judgeReport.checks.map((check) => (
            <div key={check.check_name} className="p-4">
              <div className="flex items-start justify-between mb-2">
                <div className="flex items-center gap-3">
                  <span className={`w-8 h-8 rounded flex items-center justify-center text-sm font-bold ${
                    check.status === 'pass'
                      ? 'bg-green-100 text-green-800'
                      : 'bg-red-100 text-red-800'
                  }`}>
                    {check.status === 'pass' ? '✓' : '✗'}
                  </span>
                  <div>
                    <div className="font-medium text-gray-900">{check.check_name}</div>
                    <div className="text-xs text-gray-500">{check.message}</div>
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-sm font-mono">
                    {(check.score * 100).toFixed(1)}% / {(check.threshold * 100).toFixed(1)}%
                  </div>
                  <div className="text-xs text-gray-500">Score / Threshold</div>
                </div>
              </div>

              {/* Progress Bar */}
              <div className="w-full bg-gray-200 rounded-full h-2 mb-2">
                <div
                  className={`h-2 rounded-full transition-all ${
                    check.passed ? 'bg-green-600' : 'bg-red-600'
                  }`}
                  style={{ width: `${Math.min(check.score * 100, 100)}%` }}
                />
              </div>

              {/* Details */}
              {check.details && Object.keys(check.details).length > 0 && (
                <details className="mt-2">
                  <summary className="text-xs text-gray-600 cursor-pointer hover:text-gray-900">
                    View Details
                  </summary>
                  <pre className="mt-2 text-xs text-gray-700 bg-gray-50 p-3 rounded overflow-x-auto">
                    {JSON.stringify(check.details, null, 2)}
                  </pre>
                </details>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Check Categories */}
      <div className="grid grid-cols-2 gap-4">
        <div className="border border-gray-200 rounded-lg p-4">
          <h4 className="text-sm font-semibold text-gray-900 mb-2">Critical Checks</h4>
          <ul className="space-y-1 text-xs text-gray-600">
            <li>• Citation Coverage</li>
            <li>• Groundedness</li>
            <li>• Hallucination Detection</li>
            <li>• Contradiction Detection</li>
          </ul>
        </div>
        <div className="border border-gray-200 rounded-lg p-4">
          <h4 className="text-sm font-semibold text-gray-900 mb-2">Safety Checks</h4>
          <ul className="space-y-1 text-xs text-gray-600">
            <li>• PII Leakage</li>
            <li>• Toxicity</li>
            <li>• Bias Detection</li>
            <li>• Relevance</li>
            <li>• Consistency</li>
          </ul>
        </div>
      </div>
    </div>
  );
}
