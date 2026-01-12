"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { apiClient } from "@/lib/api";
import ForceGraph2D from "react-force-graph-2d";

interface GraphNode {
  id: string;
  label: string;
  type: string;
  properties: Record<string, any>;
}

interface GraphEdge {
  source: string;
  target: string;
  type: string;
  properties: Record<string, any>;
}

interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
  stats: any;
}

// Color scheme for different entity types
const NODE_COLORS: Record<string, string> = {
  // Generic entity types
  Person: "#FF6B6B",
  Organization: "#4ECDC4",
  Location: "#45B7D1",
  Date: "#FFA07A",
  Event: "#98D8C8",
  Concept: "#F7DC6F",
  Product: "#BB8FCE",
  Document: "#85C1E2",
  Term: "#E74C3C",
  Metric: "#3498DB",
  // Insurance-specific types (fallback)
  Coverage: "#FF6B6B",
  Exclusion: "#4ECDC4",
  Condition: "#45B7D1",
  Endorsement: "#FFA07A",
  Form: "#98D8C8",
  Definition: "#F7DC6F",
  State: "#BB8FCE",
  Other: "#95A5A6",
};

export function GraphTab() {
  const [graphData, setGraphData] = useState<GraphData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [selectedEdge, setSelectedEdge] = useState<GraphEdge | null>(null);
  const [isClearing, setIsClearing] = useState(false);
  const [isRebuilding, setIsRebuilding] = useState(false);
  const fgRef = useRef<any>();

  useEffect(() => {
    loadGraph();
  }, []);

  const loadGraph = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await apiClient.getGraph();
      setGraphData(data);
    } catch (err: any) {
      setError(err.message || "Failed to load graph");
      console.error("Error loading graph:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleClearGraph = async () => {
    if (!confirm("Are you sure you want to clear the entire knowledge graph? This action cannot be undone.")) {
      return;
    }

    try {
      setIsClearing(true);
      setError(null);
      await apiClient.clearGraph();
      await loadGraph();
    } catch (err: any) {
      setError(err.message || "Failed to clear graph");
      console.error("Error clearing graph:", err);
    } finally {
      setIsClearing(false);
    }
  };

  const handleRebuildGraph = async () => {
    if (!confirm("Are you sure you want to rebuild the knowledge graph from all indexed documents? This may take several minutes depending on the number of documents.")) {
      return;
    }

    try {
      setIsRebuilding(true);
      setError(null);
      const result = await apiClient.rebuildGraph("generic");
      console.log("Graph rebuilt:", result);
      await loadGraph();
    } catch (err: any) {
      setError(err.message || "Failed to rebuild graph");
      console.error("Error rebuilding graph:", err);
    } finally {
      setIsRebuilding(false);
    }
  };

  const handleNodeClick = useCallback((node: any) => {
    setSelectedNode(node);
    setSelectedEdge(null);
  }, []);

  const handleLinkClick = useCallback((link: any) => {
    setSelectedEdge(link);
    setSelectedNode(null);
  }, []);

  const handleBackgroundClick = useCallback(() => {
    setSelectedNode(null);
    setSelectedEdge(null);
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center p-12">
        <div className="text-center">
          <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-blue-600 border-r-transparent"></div>
          <p className="mt-4 text-gray-600">Loading knowledge graph...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-lg bg-red-50 border border-red-200 p-6">
        <h3 className="text-lg font-semibold text-red-900 mb-2">Error</h3>
        <p className="text-red-700">{error}</p>
        <button
          onClick={loadGraph}
          className="mt-4 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
        >
          Retry
        </button>
      </div>
    );
  }

  if (!graphData || graphData.nodes.length === 0) {
    return (
      <div className="rounded-lg bg-yellow-50 border border-yellow-200 p-6">
        <h3 className="text-lg font-semibold text-yellow-900 mb-2">No Graph Data</h3>
        <p className="text-yellow-700 mb-4">
          No entities have been extracted yet. Index some documents to build the knowledge graph.
        </p>
        <button
          onClick={handleRebuildGraph}
          disabled={isRebuilding}
          className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
        >
          {isRebuilding ? "Rebuilding..." : "Build Graph from Indexed Documents"}
        </button>
      </div>
    );
  }

  // Prepare data for react-force-graph-2d
  const forceGraphData = {
    nodes: graphData.nodes.map((node) => ({
      id: node.id,
      name: node.label,
      type: node.type,
      properties: node.properties,
      color: NODE_COLORS[node.type] || NODE_COLORS.Other,
    })),
    links: graphData.edges.map((edge) => ({
      source: edge.source,
      target: edge.target,
      type: edge.type,
      properties: edge.properties,
    })),
  };

  const entityTypeCounts: Record<string, number> = {};
  graphData.nodes.forEach((node) => {
    entityTypeCounts[node.type] = (entityTypeCounts[node.type] || 0) + 1;
  });

  return (
    <div className="space-y-6">
      {/* Info Banner */}
      {(isClearing || isRebuilding) && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex items-center gap-2">
            <div className="inline-block h-5 w-5 animate-spin rounded-full border-3 border-solid border-blue-600 border-r-transparent"></div>
            <div>
              <p className="text-sm font-medium text-blue-900">
                {isClearing && "Clearing knowledge graph..."}
                {isRebuilding && "Rebuilding knowledge graph from all indexed documents. This may take a few minutes..."}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Stats Card */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="text-sm font-medium text-blue-900">Total Nodes</div>
          <div className="text-2xl font-bold text-blue-700">{graphData.nodes.length}</div>
        </div>
        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
          <div className="text-sm font-medium text-green-900">Total Edges</div>
          <div className="text-2xl font-bold text-green-700">{graphData.edges.length}</div>
        </div>
        <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
          <div className="text-sm font-medium text-purple-900">Entity Types</div>
          <div className="text-2xl font-bold text-purple-700">
            {Object.keys(entityTypeCounts).length}
          </div>
        </div>
      </div>

      {/* Entity Type Legend */}
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
        <h3 className="text-sm font-semibold text-gray-900 mb-3">Entity Types</h3>
        <div className="flex flex-wrap gap-3">
          {Object.entries(entityTypeCounts)
            .sort((a, b) => b[1] - a[1])
            .map(([type, count]) => (
              <div key={type} className="flex items-center gap-2">
                <div
                  className="w-4 h-4 rounded-full"
                  style={{ backgroundColor: NODE_COLORS[type] || NODE_COLORS.Other }}
                />
                <span className="text-sm text-gray-700">
                  {type} <span className="text-gray-500">({count})</span>
                </span>
              </div>
            ))}
        </div>
      </div>

      {/* Graph Visualization */}
      <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
        <div className="bg-gray-50 border-b border-gray-200 px-4 py-3 flex justify-between items-center">
          <h3 className="text-lg font-semibold text-gray-900">Knowledge Graph Visualization</h3>
          <div className="flex gap-2">
            <button
              onClick={handleClearGraph}
              disabled={isClearing || isRebuilding}
              className="px-3 py-1 bg-red-600 text-white text-sm rounded hover:bg-red-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
            >
              {isClearing ? "Clearing..." : "Clear Graph"}
            </button>
            <button
              onClick={handleRebuildGraph}
              disabled={isClearing || isRebuilding}
              className="px-3 py-1 bg-green-600 text-white text-sm rounded hover:bg-green-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
            >
              {isRebuilding ? "Rebuilding..." : "Rebuild Graph"}
            </button>
            <button
              onClick={() => {
                if (fgRef.current) {
                  fgRef.current.zoomToFit(400, 50);
                }
              }}
              className="px-3 py-1 bg-blue-600 text-white text-sm rounded hover:bg-blue-700"
            >
              Fit to View
            </button>
          </div>
        </div>
        <div className="relative" style={{ height: "600px", backgroundColor: "#f9fafb" }}>
          <ForceGraph2D
            ref={fgRef}
            graphData={forceGraphData}
            nodeLabel="name"
            nodeRelSize={6}
            nodeCanvasObject={(node: any, ctx: CanvasRenderingContext2D, globalScale: number) => {
              const label = node.name;
              const fontSize = 12 / globalScale;
              ctx.font = `${fontSize}px Sans-Serif`;
              const textWidth = ctx.measureText(label).width;
              const bckgDimensions = [textWidth, fontSize].map((n) => n + fontSize * 0.4);

              // Draw node circle
              ctx.fillStyle = node.color;
              ctx.beginPath();
              ctx.arc(node.x, node.y, 5, 0, 2 * Math.PI, false);
              ctx.fill();

              // Draw label background
              ctx.fillStyle = "rgba(255, 255, 255, 0.9)";
              ctx.fillRect(
                node.x - bckgDimensions[0] / 2,
                node.y - bckgDimensions[1] / 2 + 8,
                bckgDimensions[0],
                bckgDimensions[1]
              );

              // Draw label text
              ctx.textAlign = "center";
              ctx.textBaseline = "middle";
              ctx.fillStyle = "#333";
              ctx.fillText(label, node.x, node.y + 8);
            }}
            linkLabel={(link: any) => link.type}
            linkCanvasObjectMode={() => "after"}
            linkCanvasObject={(link: any, ctx: CanvasRenderingContext2D, globalScale: number) => {
              const label = link.type;
              const fontSize = 10 / globalScale;
              ctx.font = `${fontSize}px Sans-Serif`;

              // Calculate midpoint
              const start = link.source;
              const end = link.target;
              if (typeof start !== 'object' || typeof end !== 'object') return;

              const textPos = {
                x: start.x + (end.x - start.x) / 2,
                y: start.y + (end.y - start.y) / 2
              };

              // Draw label background
              const textWidth = ctx.measureText(label).width;
              const bckgDimensions = [textWidth + fontSize * 0.4, fontSize + fontSize * 0.4];
              ctx.fillStyle = "rgba(255, 255, 255, 0.95)";
              ctx.fillRect(
                textPos.x - bckgDimensions[0] / 2,
                textPos.y - bckgDimensions[1] / 2,
                bckgDimensions[0],
                bckgDimensions[1]
              );

              // Draw label text
              ctx.textAlign = "center";
              ctx.textBaseline = "middle";
              ctx.fillStyle = "#555";
              ctx.font = `${fontSize}px Sans-Serif`;
              ctx.fillText(label, textPos.x, textPos.y);
            }}
            linkDirectionalArrowLength={3.5}
            linkDirectionalArrowRelPos={1}
            linkCurvature={0.1}
            linkColor={() => "#7F8C8D"}
            linkWidth={2}
            onNodeClick={handleNodeClick}
            onLinkClick={handleLinkClick}
            onBackgroundClick={handleBackgroundClick}
            d3VelocityDecay={0.3}
            cooldownTime={3000}
          />
        </div>
      </div>

      {/* Node Details Panel */}
      {selectedNode && (
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Node Details</h3>
          <div className="space-y-3">
            <div>
              <span className="text-sm font-medium text-gray-600">Label:</span>
              <span className="ml-2 text-sm text-gray-900">{selectedNode.label}</span>
            </div>
            <div>
              <span className="text-sm font-medium text-gray-600">Type:</span>
              <span className="ml-2">
                <span
                  className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium"
                  style={{
                    backgroundColor: NODE_COLORS[selectedNode.type] || NODE_COLORS.Other,
                    color: "white",
                  }}
                >
                  {selectedNode.type}
                </span>
              </span>
            </div>
            <div>
              <span className="text-sm font-medium text-gray-600">ID:</span>
              <span className="ml-2 text-sm font-mono text-gray-700">{selectedNode.id}</span>
            </div>
            {Object.keys(selectedNode.properties || {}).length > 0 && (
              <div>
                <span className="text-sm font-medium text-gray-600">Properties:</span>
                <div className="mt-2 bg-gray-50 rounded p-3">
                  <pre className="text-xs text-gray-800 whitespace-pre-wrap">
                    {JSON.stringify(selectedNode.properties, null, 2)}
                  </pre>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Edge Details Panel */}
      {selectedEdge && (
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Relationship Details</h3>
          <div className="space-y-3">
            <div>
              <span className="text-sm font-medium text-gray-600">Type:</span>
              <span className="ml-2 text-sm font-semibold text-gray-900">{selectedEdge.type}</span>
            </div>
            <div>
              <span className="text-sm font-medium text-gray-600">Source:</span>
              <span className="ml-2 text-sm text-gray-900">{selectedEdge.source}</span>
            </div>
            <div>
              <span className="text-sm font-medium text-gray-600">Target:</span>
              <span className="ml-2 text-sm text-gray-900">{selectedEdge.target}</span>
            </div>
            {Object.keys(selectedEdge.properties || {}).length > 0 && (
              <div>
                <span className="text-sm font-medium text-gray-600">Properties:</span>
                <div className="mt-2 bg-gray-50 rounded p-3">
                  <pre className="text-xs text-gray-800 whitespace-pre-wrap">
                    {JSON.stringify(selectedEdge.properties, null, 2)}
                  </pre>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
