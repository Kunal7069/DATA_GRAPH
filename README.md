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
