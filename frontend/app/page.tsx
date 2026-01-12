"use client";

import { useState } from "react";
import { TabType, Event, RunData } from "@/lib/types";
import { apiClient } from "@/lib/api";

// Import tab components
import { QueryTab } from "@/components/QueryTab";
import { RetrievalTab } from "@/components/RetrievalTab";
import { FusionTab } from "@/components/FusionTab";
import { ContextTab } from "@/components/ContextTab";
import { AnswerTab } from "@/components/AnswerTab";
import { JudgeTab } from "@/components/JudgeTab";
import { EventsTab } from "@/components/EventsTab";
import { ConfigTab } from "@/components/ConfigTab";
import { DocumentsTab } from "@/components/DocumentsTab";
import { GraphTab } from "@/components/GraphTab";

export default function Home() {
  const [activeTab, setActiveTab] = useState<TabType>("query");
  const [currentRunId, setCurrentRunId] = useState<string | null>(null);
  const [currentQuery, setCurrentQuery] = useState<string>("");
  const [runData, setRunData] = useState<RunData | null>(null);
  const [events, setEvents] = useState<Event[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);

  const tabs: { id: TabType; label: string }[] = [
    { id: "query", label: "Query" },
    { id: "retrieval", label: "Retrieval" },
    { id: "fusion", label: "Fusion" },
    { id: "context", label: "Context" },
    { id: "answer", label: "Answer" },
    { id: "judge", label: "Judge" },
    { id: "events", label: "Events" },
    { id: "config", label: "Config" },
    { id: "documents", label: "Documents" },
    { id: "graph", label: "Graph" },
  ];

  const handleRunStart = async (runId: string, query: string) => {
    setCurrentRunId(runId);
    setCurrentQuery(query);
    setEvents([]);
    setRunData(null);
    startEventStream(runId);
    pollRunStatus(runId);
  };

  const startEventStream = (runId: string) => {
    setIsStreaming(true);
    const eventSource = apiClient.createEventSource(runId);

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === "connected") {
          console.log("SSE connected");
        } else if (data.type === "run_complete") {
          eventSource.close();
          setIsStreaming(false);
          loadRunData(runId);
        } else if (data.type === "error") {
          eventSource.close();
          setIsStreaming(false);
        } else {
          setEvents((prev) => [...prev, data as Event]);
        }
      } catch (err) {
        console.error("Error parsing SSE event:", err);
      }
    };

    eventSource.onerror = () => {
      eventSource.close();
      setIsStreaming(false);
    };
  };

  const pollRunStatus = async (runId: string) => {
    let attempts = 0;
    const maxAttempts = 60;

    const poll = async () => {
      try {
        const data = await apiClient.getRunStatus(runId);
        if (data.events) {
          setEvents(data.events);
        }
        if (data.status === "completed" || data.status === "failed" || data.status === "blocked") {
          setRunData({
            run_id: runId,
            query: currentQuery,
            status: data.status,
            artifacts: data.artifacts || {},
            events: data.events || [],
          });
          setIsStreaming(false);
          return;
        }
        if (attempts < maxAttempts) {
          attempts++;
          setTimeout(poll, 5000);
        }
      } catch (err) {
        setIsStreaming(false);
      }
    };

    setTimeout(poll, 10000);
  };

  const loadRunData = async (runId: string) => {
    try {
      const data = await apiClient.getRunStatus(runId);
      setRunData({
        run_id: runId,
        query: currentQuery,
        status: data.status,
        artifacts: data.artifacts || {},
        events: data.events || [],
      });
    } catch (err) {
      console.error("Error loading run data:", err);
    }
  };

  const renderTabContent = () => {
    switch (activeTab) {
      case "query":
        return (
          <QueryTab
            onRunStart={handleRunStart}
            currentQuery={currentQuery}
            runData={runData}
            isStreaming={isStreaming}
          />
        );
      case "retrieval":
        return <RetrievalTab retrievalBundle={runData?.artifacts.retrieval_bundle || null} />;
      case "fusion":
        return <FusionTab fusedResults={runData?.artifacts.fused_results || null} />;
      case "context":
        return <ContextTab contextPack={runData?.artifacts.context_pack || null} />;
      case "answer":
        return (
          <AnswerTab
            answer={runData?.artifacts.answer || null}
            judgeReport={runData?.artifacts.judge_report || null}
          />
        );
      case "judge":
        return <JudgeTab judgeReport={runData?.artifacts.judge_report || null} />;
      case "events":
        return <EventsTab runId={currentRunId} events={events} />;
      case "config":
        return <ConfigTab />;
      case "documents":
        return <DocumentsTab />;
      case "graph":
        return <GraphTab />;
      default:
        return <div>Tab not implemented</div>;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-200">
        <div className="px-6 py-4">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">RAGMesh</h1>
              <p className="text-sm text-gray-600">
                Production-Grade Insurance RAG Framework
              </p>
            </div>
            {currentRunId && (
              <div className="text-right">
                <div className="text-xs text-gray-500">Current Run</div>
                <div className="text-sm font-mono text-gray-700">{currentRunId}</div>
                {isStreaming && (
                  <div className="flex items-center gap-2 text-xs text-green-600 mt-1">
                    <span className="w-2 h-2 bg-green-600 rounded-full animate-pulse" />
                    Streaming
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </header>

      <div className="border-b border-gray-200 bg-white">
        <nav className="flex px-6 overflow-x-auto">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-4 py-3 text-sm font-medium whitespace-nowrap border-b-2 transition-colors ${
                activeTab === tab.id
                  ? "border-blue-500 text-blue-600"
                  : "border-transparent text-gray-600 hover:text-gray-900 hover:border-gray-300"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      <main className="p-6">
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 max-w-7xl mx-auto">
          {renderTabContent()}
        </div>
      </main>
    </div>
  );
}
