# Flask Graph API

## 1. `crud_api.py`

This file handles CRUD operations for nodes, edges, and graphs. It defines routes to:

- **Create nodes and edges**: Manage the creation of graph components.
- **Validate relationships**: Ensure data integrity between connected nodes.
- **Create a graph**: Formulate a graph from multiple nodes.
- **Retrieve graph structure**: Output the adjacency list that illustrates node connections.

### Key Methods:

- `create_node()`: Validates the node's data and creates it in MongoDB if validation passes.
- `create_edge()`: Checks the existence of source and destination nodes, validating data type compatibility before saving the edge.
- `create_graph()`: Verifies that all nodes in a provided list exist before graph creation.
- `get_graph()`: Retrieves the graph data and constructs an adjacency list showing nodes and their connected edges.

## 2. `graph_api.py`

This file defines classes and logic for processing graphs:

- **Node_1, Edge_1, and Graph_1 classes**: For in-memory processing and validation of nodes, edges, and the overall graph structure.
- **Graph_1 methods**: Facilitate the addition of nodes and edges, processing of relationships, and the creation of an adjacency list.

### Key Methods:

- `add_node()`: Adds a node to the graph, initializing `data_in` and `data_out` fields based on the provided types.
- `add_edge()`: Creates an edge between two nodes and validates the data keys in `src_to_dst_data_keys`.
- `process_graph()`: Implements a topological sorting approach to set node levels and transfer `data_out` values based on edge relationships.
- `get_graph_state()`: Retrieves the state of the graph post-processing, displaying each node’s data and hierarchical relationships.

## Integration

Both files connect to the same MongoDB database and work together by:

- **Storing nodes and edges** in `crud_api.py`.
- **Utilizing these stored nodes and edges** to construct an in-memory graph representation in `graph_api.py`.
- The `process_graph()` method updates each node's data in the in-memory graph to simulate data flow across nodes.

## Getting Started

### Prerequisites

- Python 3.8 or higher
- A running MongoDB instance
- Required Python packages (listed in `requirements.txt`)

### Setup Instructions

1. **Clone the repository**:
   ```bash
   git clone https://github.com/Kunal7069/DATA_GRAPH
2. **Install the dependencies**:
   ```bash
   pip install requirements.txt
3. **Edit the .env file**:
   ```bash
   Paste your mongodb cloud url in MONGO_URI in .env file
3. **Run the project**:
   ```bash
   python app.py




# Graph Implementation Documentation

## Overview
This document provides a detailed explanation of the graph implementation designed for managing data flow and dependencies between nodes. The implementation uses a directed graph structure with support for topological sorting, dynamic node/edge management, and runtime data handling.

## Table of Contents
1. Data Structures
2. Core Components
3. Algorithm Analysis
4. Time & Space Complexity
5. Optimization Decisions
6. Usage Examples
7. Best Practices

## 1. Data Structures

### 1.1 Primary Classes

#### Edge Class
```python
@dataclass
class Edge:
    edge_id: str
    src_node: str
    dst_node: str
    src_to_dst_data_keys: Dict[str, str]
```
- Represents directed edges between nodes
- Maps source node data keys to destination node data keys
- Implemented as a dataclass for automatic initialization and better memory management

#### Node Class
```python
@dataclass
class Node:
    node_id: str
    data_in: Dict[str, str]
    data_out: Dict[str, str]
    runtime_data: Dict[str, Any]
```
- Represents graph nodes with input/output interfaces
- Maintains runtime data separately from structural data
- Uses default_factory for dynamic dictionary creation

### 1.2 Graph Class Properties
- `nodes`: Dictionary mapping node IDs to Node objects
- `edges`: Dictionary mapping edge IDs to Edge objects
- `directed_adj`: Adjacency list for directed edges
- `undirected_adj`: Adjacency list for undirected connections
- `indegree`: Counter for incoming edges per node
- `dependent_on`: Tracks node dependencies

## 2. Core Components

### 2.1 Node Management
- **Addition**: O(1) operation with duplicate checking
- **Removal**: O(E) operation where E is the number of edges
- **Data Updates**: O(1) runtime data modification

### 2.2 Edge Management
- **Addition**: O(1) operation with validation
- **Removal**: O(1) operation with adjacency list updates
- **Dependency Tracking**: Automatic updating of indegree counts

### 2.3 Graph Processing
- Connectivity checking using DFS
- Topological sorting with level-wise processing
- Cycle detection during processing

## 3. Algorithm Analysis

### 3.1 Depth-First Search (is_connected)
```python
def is_connected(self) -> bool:
    if not self.nodes:
        return True
    start_node = next(iter(self.nodes))
    visited = set()
    def dfs(node: str):
        visited.add(node)
        for neighbor in self.undirected_adj[node]:
            if neighbor not in visited:
                dfs(neighbor)
    dfs(start_node)
    return len(visited) == len(self.nodes)
```
- Uses recursive DFS for connectivity checking
- Validates graph connectivity in undirected context
- Handles empty graph cases efficiently

### 3.2 Topological Sort (process_graph)
```python
def process_graph(self) -> Tuple[List[List[str]], bool]:
    topo_order = []
    indegree_copy = deepcopy(self.indegree)
    current_nodes = [
        node_id for node_id in self.nodes 
        if indegree_copy[node_id] == 0
    ]
    # ... processing logic
    return topo_order, is_not_cyclic
```
- Modified Kahn's algorithm for level-wise processing
- Maintains lexicographical ordering within levels
- Detects cycles during processing

## 4. Time & Space Complexity

4. Time & Space Complexity
4.1 Time Complexity
•	Node Addition: O(1)
•	Node Removal: O(E) where E is number of edges
•	Edge Addition: O(1)
•	Edge Removal: O(1)
•	Connectivity Check: O(V + E) where V is number of vertices
•	Topological Sort: O(E + VlogV) 
o	O(E) for processing all edges
o	O(VlogV) for sorting nodes at each level
o	The sort operation on nodes is performed at each level, and in worst case, we might need to sort V nodes
•	Graph Validation: O(E + VlogV) (dominated by topological sort)

### 4.2 Space Complexity
- Adjacency Lists: O(V + E)
- Node Storage: O(V)
- Edge Storage: O(E)
- Processing Storage: O(V) for visited sets and queues
- Total Space: O(V + E)

## 5. Optimization Decisions

### 5.1 Data Structure Choices
- **Adjacency Lists vs Matrix**: Adjacency lists chosen for sparse graphs optimization
- **Dual Adjacency Lists**: Separate directed/undirected for efficient traversal
- **Dictionary Storage**: O(1) access time for nodes and edges
- **defaultdict Usage**: Reduces error checking overhead

### 5.2 Algorithm Optimizations
1.	**DFS Implementation**
a.	Recursive approach for clear code and stack management
b.	Set-based visited tracking for O(1) lookups
c.	Early termination when all nodes are visited

2.	Topological Sort 
a.	Level-wise processing for parallel execution potential
b.	In-place indegree modification
c.	Lexicographical ordering maintenance using sorting: O(VlogV)
d.	The sorting overhead is accepted to maintain consistent ordering of nodes at each level
e.	Trade-off: We sacrifice some performance (moving from O(V + E) to O(E + VlogV)) to maintain lexicographical ordering
f.	Alternative approaches could use priority queue for O(VlogV + E) but with more complex implementation


3. **Edge Management**
   - Bidirectional mapping for undirected access
   - Efficient edge removal with O(1) lookup
   - Automatic dependency tracking

## 6. Usage Examples

### 6.1 Basic Usage
```python
# Create graph
graph = Graph()

# Add nodes
graph.add_node("node1", {
    "data_in": {"key1": "int"},
    "data_out": {"key2": "str"}
})

# Add edges
graph.add_edge({
    "edge_id": "edge1",
    "src_node": "node1",
    "dst_node": "node2",
    "src_to_dst_data_keys": {"key1": "key2"}
})

# Process graph
graph.process_and_validate()
```

### 6.2 Runtime Data Management
```python
# Set data
graph.set_node_data("node1", "key1", 42)

# Remove components
graph.remove_node("node1")
graph.remove_edge("edge1")
```

## 7. Best Practices

### 7.1 Graph Construction
1. Add all nodes before edges
2. Validate node existence before edge addition
3. Maintain unique identifiers for nodes and edges
4. Check return values for operation success

### 7.2 Data Management
1. Use appropriate data types in data_in/data_out
2. Keep runtime_data separate from structural data
3. Clear runtime_data when reprocessing
4. Validate data type consistency

### 7.3 Error Handling
1. Check connectivity before processing
2. Validate cycle presence
3. Handle node/edge removal carefully
4. Maintain data consistency during updates



## Conclusion
This implementation provides an efficient, flexible, and maintainable solution for managing directed graphs with data flow requirements. The chosen data structures and algorithms provide optimal performance for most common operations while maintaining code clarity and extensibility. The level-wise topological sorting feature enables parallel processing potential, making it suitable for various applications including data processing pipelines, workflow management, and dependency resolution systems.
