/**
 * Query Tab - Query input and execution
 */

import { useState, useEffect } from 'react';
import { apiClient, RunRequest } from '@/lib/api';
import { RunData, ChatTurn } from '@/lib/types';

interface QueryTabProps {
  onRunStart: (runId: string, query: string) => void;
  currentQuery: string;
  runData: RunData | null;
  isStreaming: boolean;
}

export function QueryTab({ onRunStart, currentQuery, runData, isStreaming }: QueryTabProps) {
  const [query, setQuery] = useState('');
  const [workflowId, setWorkflowId] = useState('default_workflow');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Chat mode state
  const [mode, setMode] = useState<'query' | 'chat'>('query');
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [chatHistory, setChatHistory] = useState<ChatTurn[]>([]);

  // Update chat history when runData changes in chat mode
  useEffect(() => {
    if (mode === 'chat' && runData?.session_id && runData.artifacts?.answer) {
      const answer = runData.artifacts.answer as any;

      // Check if this turn already exists in history
      setChatHistory(prev => {
        const alreadyExists = prev.some(t => t.run_id === runData.run_id);
        if (alreadyExists) {
          return prev; // Don't add duplicates
        }

        const newTurn: ChatTurn = {
          turn_number: runData.turn_number || prev.length + 1,
          query: currentQuery,
          answer: answer,
          run_id: runData.run_id,
          timestamp: new Date().toISOString(),
          tokens: 0, // Not tracking tokens on frontend
        };

        return [...prev, newTurn];
      });
    }
  }, [runData, mode, currentQuery]);

  // Handle mode switching
  const handleModeSwitch = (newMode: 'query' | 'chat') => {
    setMode(newMode);
    if (newMode === 'query') {
      // Clear chat state when switching back to query mode
      setSessionId(null);
      setChatHistory([]);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);

    try {
      const request: RunRequest = {
        query: query.trim(),
        workflow_id: workflowId,
        mode: mode,
        session_id: mode === 'chat' ? sessionId || undefined : undefined,
        chat_profile_id: mode === 'chat' ? 'default' : undefined,
      };

      const response = await apiClient.executeRun(request);

      // Handle session termination (user typed "quit")
      if (response.status === 'terminated') {
        setSessionId(null);
        setChatHistory([]);
        setQuery('');
        setError('Chat session ended.');
        return;
      }

      // Store session_id for chat mode
      if (mode === 'chat' && response.session_id) {
        setSessionId(response.session_id);
      }

      onRunStart(response.run_id, query);

      // Clear input
      setQuery('');
    } catch (err: any) {
      setError(err.message || 'Failed to execute query');
    } finally {
      setIsSubmitting(false);
    }
  };

  const answer = runData?.artifacts?.answer as any;
  const judgeReport = runData?.artifacts?.judge_report;
  const answerText = answer?.answer_text ?? answer?.answer ?? '';
  const citations = Array.isArray(answer?.citations) ? answer.citations : [];
  const assumptions = Array.isArray(answer?.assumptions) ? answer.assumptions : [];
  const limitations = Array.isArray(answer?.limitations) ? answer.limitations : [];
  const confidence = answer?.confidence ?? 'low';
  const isBlocked = judgeReport?.decision === 'FAIL_BLOCKED';

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Execute Query</h2>
        <p className="text-sm text-gray-600 mb-6">
          Enter a question and select a workflow to execute the RAG pipeline.
        </p>
      </div>

      {/* Mode Toggle */}
      <div className="flex gap-2 bg-gray-100 p-1 rounded-lg w-fit">
        <button
          type="button"
          onClick={() => handleModeSwitch('query')}
          className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
            mode === 'query'
              ? 'bg-white text-blue-600 shadow-sm'
              : 'text-gray-600 hover:text-gray-900'
          }`}
          disabled={isSubmitting}
        >
          Query Mode
        </button>
        <button
          type="button"
          onClick={() => handleModeSwitch('chat')}
          className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
            mode === 'chat'
              ? 'bg-white text-blue-600 shadow-sm'
              : 'text-gray-600 hover:text-gray-900'
          }`}
          disabled={isSubmitting}
        >
          Chat Mode
        </button>
      </div>

      {/* Chat History Panel (visible in chat mode) */}
      {mode === 'chat' && (
        <div className="border border-gray-300 rounded-lg bg-white">
          <div className="px-4 py-3 border-b border-gray-300 bg-gray-50">
            <div className="flex items-center justify-between">
              <div className="text-sm font-semibold text-gray-900">Conversation</div>
              <div className="text-xs text-gray-500">
                {sessionId ? (
                  <>Session: {sessionId.slice(0, 8)}... • {chatHistory.length} turn{chatHistory.length !== 1 ? 's' : ''}</>
                ) : (
                  'No active session'
                )}
              </div>
            </div>
          </div>
          <div className="p-4 max-h-[500px] overflow-y-auto space-y-4">
            {chatHistory.length === 0 ? (
              <div className="text-sm text-gray-500 text-center py-8">
                Start a conversation by asking a question below...
              </div>
            ) : (
              chatHistory.map((turn, idx) => (
                <div key={turn.run_id} className="space-y-3">
                  {/* User Question */}
                  <div className="flex justify-end">
                    <div className="bg-blue-100 rounded-lg px-4 py-2 max-w-[85%]">
                      <div className="text-xs text-blue-600 font-medium mb-1">You</div>
                      <div className="text-sm text-gray-900">{turn.query}</div>
                    </div>
                  </div>
                  {/* Assistant Answer */}
                  <div className="flex justify-start">
                    <div className="bg-gray-100 rounded-lg px-4 py-2 max-w-[85%]">
                      <div className="text-xs text-gray-600 font-medium mb-1">Assistant</div>
                      <div className="text-sm text-gray-900 whitespace-pre-wrap">
                        {turn.answer?.answer || turn.answer?.answer_text || 'No answer'}
                      </div>
                      {turn.answer?.confidence && (
                        <div className="flex items-center gap-2 mt-2">
                          <span className="text-xs text-gray-500">Confidence:</span>
                          <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                            turn.answer.confidence === 'high'
                              ? 'bg-green-100 text-green-800'
                              : turn.answer.confidence === 'medium'
                                ? 'bg-yellow-100 text-yellow-800'
                                : 'bg-red-100 text-red-800'
                          }`}>
                            {String(turn.answer.confidence).charAt(0).toUpperCase() + String(turn.answer.confidence).slice(1)}
                          </span>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      )}

      {/* Session Status in Chat Mode */}
      {mode === 'chat' && (
        <div className="bg-blue-50 border border-blue-200 rounded-md p-3">
          <p className="text-sm text-blue-800">
            {sessionId
              ? `Active chat session. Type 'Quit' to end the session.`
              : 'No active session. Submit a query to start a new chat session.'}
          </p>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Query Input */}
        <div>
          <label htmlFor="query" className="block text-sm font-medium text-gray-700 mb-2">
            Query
          </label>
          <textarea
            id="query"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder={
              mode === 'chat'
                ? "Continue the conversation... (Type 'Quit' to end session)"
                : "e.g., What are the exclusions for flood damage in California homeowners insurance?"
            }
            rows={4}
            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 text-gray-900"
            required
            disabled={isSubmitting}
            title={
              mode === 'chat'
                ? "Continue the chat conversation. The system remembers previous Q&As in this session."
                : "Enter your insurance-related question here. The RAG pipeline will search through indexed documents to find relevant information."
            }
          />
        </div>

        {/* Workflow Selection */}
        <div>
          <label htmlFor="workflow" className="block text-sm font-medium text-gray-700 mb-2">
            Workflow Profile
          </label>
          <select
            id="workflow"
            value={workflowId}
            onChange={(e) => setWorkflowId(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 text-gray-900"
            disabled={isSubmitting}
            title="Select a workflow profile: Default (balanced tri-modal), Fast (vector only), or Comprehensive (with reranking)"
          >
            <option value="default_workflow">Default (Balanced)</option>
            <option value="fast_workflow">Fast (Vector Only)</option>
            <option value="comprehensive_workflow">Comprehensive (With Reranking)</option>
          </select>
        </div>

        {/* Error Display */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-md p-4">
            <p className="text-sm text-red-800">{error}</p>
          </div>
        )}

        {/* Submit Button */}
        <div className="flex justify-end">
          <button
            type="submit"
            disabled={isSubmitting || !query.trim()}
            className="px-6 py-2 bg-blue-600 text-white font-medium rounded-md shadow-sm hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isSubmitting ? 'Executing...' : 'Execute Query'}
          </button>
        </div>
      </form>

      {/* Inline Answer */}
      {currentQuery && (
        <div className="border border-gray-200 rounded-lg bg-white">
          <div className="flex items-center justify-between px-4 py-3 border-b border-gray-200">
            <div>
              <div className="text-sm font-semibold text-gray-900">Latest Result</div>
              <div className="text-xs text-gray-500">{currentQuery}</div>
            </div>
            <div className="text-xs text-gray-500">
              {isStreaming ? 'Running...' : runData?.status || 'idle'}
            </div>
          </div>
          <div className="p-4 space-y-4">
            {isBlocked && (
              <div className="border border-red-200 bg-red-50 rounded-md px-3 py-2 text-xs text-red-800">
                This answer was blocked by the judge. Review the Judge tab for violations and use with caution.
              </div>
            )}
            {!answerText && (
              <div className="text-sm text-gray-500">
                {isStreaming ? 'Generating answer...' : 'No answer available yet.'}
              </div>
            )}
            {answerText && (
              <div className="space-y-3">
                <div className="flex items-center gap-2">
                  <span className="text-xs text-gray-500">Confidence:</span>
                  <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                    confidence === 'high'
                      ? 'bg-green-100 text-green-800'
                      : confidence === 'medium'
                        ? 'bg-yellow-100 text-yellow-800'
                        : 'bg-red-100 text-red-800'
                  }`}>
                    {String(confidence).charAt(0).toUpperCase() + String(confidence).slice(1)}
                  </span>
                </div>
                <p className="text-sm text-gray-900 whitespace-pre-wrap">{answerText}</p>
                {citations.length > 0 && (
                  <div className="border border-gray-200 rounded-md">
                    <div className="px-3 py-2 border-b border-gray-200 text-xs font-semibold text-gray-700">
                      Citations ({citations.length})
                    </div>
                    <div className="divide-y divide-gray-200">
                      {citations.map((citation: any, idx: number) => (
                        <div key={`${citation.chunk_id}-${idx}`} className="px-3 py-2 text-xs text-gray-700">
                          <div className="font-medium text-gray-900">[{idx + 1}] {citation.quote ?? citation.text ?? ''}</div>
                          <div className="text-gray-500">
                            Doc: {citation.doc_id} • Page: {citation.page_no ?? citation.page_number}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
                {assumptions.length > 0 && (
                  <div className="border border-yellow-200 bg-yellow-50 rounded-md px-3 py-2 text-xs text-yellow-900">
                    Assumptions: {assumptions.join('; ')}
                  </div>
                )}
                {limitations.length > 0 && (
                  <div className="border border-orange-200 bg-orange-50 rounded-md px-3 py-2 text-xs text-orange-900">
                    Limitations: {limitations.join('; ')}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Example Queries */}
      <div className="mt-8 pt-6 border-t border-gray-200">
        <h3 className="text-sm font-medium text-gray-900 mb-3">Example Queries</h3>
        <div className="space-y-2">
          {[
            'What are the coverage limits for water damage in Form HO-3?',
            'Which states require earthquake insurance?',
            'What exclusions apply to liability coverage?',
            'What are the conditions for filing a claim within 30 days?',
          ].map((example) => (
            <button
              key={example}
              onClick={() => setQuery(example)}
              className="block w-full text-left px-4 py-2 text-sm text-gray-700 bg-gray-50 rounded-md hover:bg-gray-100 transition-colors"
              disabled={isSubmitting}
            >
              {example}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
