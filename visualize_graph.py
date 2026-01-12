"""
Graph Visualization Script
Visualizes the entity graph created during indexing
"""

import json
import networkx as nx
import matplotlib.pyplot as plt
from pathlib import Path
from collections import defaultdict

def load_graph_data(graph_dir: Path):
    """Load nodes and edges from JSONL files"""
    nodes = []
    edges = []

    # Load nodes
    nodes_file = graph_dir / "nodes.jsonl"
    if nodes_file.exists():
        with open(nodes_file, 'r') as f:
            for line in f:
                if line.strip():
                    nodes.append(json.loads(line))

    # Load edges
    edges_file = graph_dir / "edges.jsonl"
    if edges_file.exists():
        with open(edges_file, 'r') as f:
            for line in f:
                if line.strip():
                    edges.append(json.loads(line))

    return nodes, edges

def create_visualization(nodes, edges, output_file="graph_visualization.png"):
    """Create and save graph visualization"""

    # Create directed graph
    G = nx.DiGraph()

    # Add nodes with attributes
    for node in nodes:
        G.add_node(
            node['node_id'],
            label=node['label'],
            node_type=node['node_type'],
            properties=node.get('properties', {})
        )

    # Add edges with attributes
    for edge in edges:
        G.add_edge(
            edge['source'],
            edge['target'],
            edge_type=edge.get('edge_type', 'UNKNOWN'),
            properties=edge.get('properties', {})
        )

    # Count entity types
    entity_type_counts = defaultdict(int)
    for node in nodes:
        entity_type_counts[node['node_type']] += 1

    # Print statistics
    print("\n" + "="*60)
    print("GRAPH STATISTICS")
    print("="*60)
    print(f"Total Nodes: {len(nodes)}")
    print(f"Total Edges: {len(edges)}")
    print(f"\nEntity Type Distribution:")
    for entity_type, count in sorted(entity_type_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {entity_type}: {count}")

    # Print node details
    print(f"\n{'='*60}")
    print("NODE DETAILS")
    print("="*60)
    for node in nodes:
        props = node.get('properties', {})
        props_str = f" - {props}" if props else ""
        print(f"[{node['node_type']}] {node['label']}{props_str}")

    # Print edge details
    print(f"\n{'='*60}")
    print("RELATIONSHIP DETAILS")
    print("="*60)
    if edges:
        for edge in edges:
            source_label = next((n['label'] for n in nodes if n['node_id'] == edge['source']), edge['source'])
            target_label = next((n['label'] for n in nodes if n['node_id'] == edge['target']), edge['target'])
            edge_type = edge.get('edge_type', 'UNKNOWN')
            print(f"{source_label} --[{edge_type}]--> {target_label}")
    else:
        print("No edges found in graph")

    # Create visualization
    fig, ax = plt.subplots(figsize=(16, 12))

    # Define colors for different entity types
    color_map = {
        'Coverage': '#FF6B6B',
        'Exclusion': '#4ECDC4',
        'Condition': '#45B7D1',
        'Endorsement': '#FFA07A',
        'Form': '#98D8C8',
        'Definition': '#F7DC6F',
        'State': '#BB8FCE',
        'Term': '#85C1E2',
        'Other': '#95A5A6'
    }

    # Get node colors based on type
    node_colors = [color_map.get(G.nodes[node]['node_type'], '#95A5A6') for node in G.nodes()]

    # Use spring layout for better spacing
    pos = nx.spring_layout(G, k=2, iterations=50, seed=42)

    # Draw nodes
    nx.draw_networkx_nodes(
        G, pos,
        node_color=node_colors,
        node_size=3000,
        alpha=0.9,
        ax=ax
    )

    # Draw edges
    nx.draw_networkx_edges(
        G, pos,
        edge_color='#7F8C8D',
        arrows=True,
        arrowsize=20,
        arrowstyle='->',
        width=2,
        alpha=0.6,
        ax=ax,
        connectionstyle='arc3,rad=0.1'
    )

    # Draw labels
    labels = {node: G.nodes[node]['label'] for node in G.nodes()}
    nx.draw_networkx_labels(
        G, pos,
        labels,
        font_size=10,
        font_weight='bold',
        ax=ax
    )

    # Draw edge labels
    edge_labels = {(e[0], e[1]): e[2].get('edge_type', '') for e in G.edges(data=True)}
    nx.draw_networkx_edge_labels(
        G, pos,
        edge_labels,
        font_size=8,
        ax=ax
    )

    # Create legend
    legend_elements = [
        plt.Line2D([0], [0], marker='o', color='w',
                   markerfacecolor=color, markersize=10, label=entity_type)
        for entity_type, color in color_map.items()
        if entity_type in entity_type_counts
    ]
    ax.legend(handles=legend_elements, loc='upper left', title='Entity Types')

    ax.set_title('Insurance Document Knowledge Graph', fontsize=16, fontweight='bold', pad=20)
    ax.axis('off')

    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"\n{'='*60}")
    print(f"Visualization saved to: {output_file}")
    print("="*60 + "\n")
    plt.close()

def main():
    """Main function"""
    graph_dir = Path("data/graph")

    if not graph_dir.exists():
        print(f"Error: Graph directory not found at {graph_dir}")
        print("Please run indexing first to generate the graph.")
        return

    nodes, edges = load_graph_data(graph_dir)

    if not nodes:
        print("No nodes found in graph. Please run indexing first.")
        return

    create_visualization(nodes, edges)

if __name__ == "__main__":
    main()
