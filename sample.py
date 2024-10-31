from flask import Flask, request, jsonify
from typing import Dict, List, Union, Optional
from collections import defaultdict, deque
from dataclasses import dataclass
from models import *
from copy import deepcopy

app = Flask(__name__)

# Type definitions
DataType = Union[int, str, bool, list, dict]

@dataclass
class Edge:
    edge_id: str
    src_node: str
    dst_node: str
    src_to_dst_data_keys: Dict[str, str]

class Node:
    def __init__(self, node_id: str, data_in: Dict[str, str], data_out: Dict[str, str]):
        self.node_id = node_id
        self.data_in = {}
        self.data_out = {}
        self.data_in_types = data_in
        self.data_out_types = data_out
        self.level = -1
        self.visited = False
        self.edges_out: List[Edge] = []

class Graph:
    def __init__(self):
        self.nodes: Dict[str, Node] = {}
        self.edges: List[Edge] = []
    
    def add_node(self, node_id: str, node_data: dict) -> None:
        data_out = node_data.get("data_out", {})
        for key, type_str in node_data["data_in"].items():
            if key not in data_out:
                data_out[key] = type_str
                
        node = Node(
            node_id=node_id,
            data_in=node_data["data_in"],
            data_out=data_out
        )
        self.nodes[node_id] = node
        for dictionary in [node.data_in, node.data_out]:
            for key, type_str in node_data["data_in"].items():
                if type_str == "int":
                    dictionary[key] = 0
                elif type_str == "str":
                    dictionary[key] = ""
                elif type_str == "bool":
                    dictionary[key] = False
                elif type_str == "list":
                    dictionary[key] = []
                elif type_str == "dict":
                    dictionary[key] = {}
    
    def add_edge(self, edge_data: dict) -> None:
        edge = Edge(
            edge_id=edge_data["edge_id"],
            src_node=edge_data["src_node"],
            dst_node=edge_data["dst_node"],
            src_to_dst_data_keys=edge_data["src_to_dst_data_keys"]
        )
        self.edges.append(edge)
        self.nodes[edge.src_node].edges_out.append(edge)
    
    def process_graph(self) -> None:
        in_degree = defaultdict(int)
        for edge in self.edges:
            in_degree[edge.dst_node] += 1
        
        queue = deque()
        for node_id in self.nodes:
            if in_degree[node_id] == 0:
                queue.append(node_id)
                self.nodes[node_id].level = 0
        
        current_level = 0
        while queue:
            level_size = len(queue)
            for _ in range(level_size):
                current_node_id = queue.popleft()
                current_node = self.nodes[current_node_id]
                
                if current_node.visited:
                    continue
                
                current_node.visited = True
                current_node.data_out = deepcopy(current_node.data_in)
                
                for edge in current_node.edges_out:
                    dst_node = self.nodes[edge.dst_node]
                    for src_key, dst_key in edge.src_to_dst_data_keys.items():
                        if not dst_node.visited:
                            dst_node.data_in[dst_key] = deepcopy(current_node.data_out[src_key])
                    in_degree[edge.dst_node] -= 1
                    if in_degree[edge.dst_node] == 0:
                        queue.append(edge.dst_node)
                        dst_node.level = current_level + 1
            current_level += 1

    def get_graph_state(self) -> Dict:
        state = {}
        for node_id, node in sorted(self.nodes.items()):
            state[node_id] = {
                "level": node.level,
                "visited": node.visited,
                "data_in": node.data_in,
                "data_out": node.data_out
            }
        return state



@app.route('/process_graph', methods=['POST'])
def process_graph_endpoint():
    data = request.get_json()
    
    adjacency_list = data.get("adjacency_list", {})
    edge_list = data.get("edge_list", [])
    graph_id = data.get("graph_id")
    input_values = data.get("input_values", {})
    
    graph = Graph()
    
    # Add nodes from adjacency list
    for node_id, node_data in adjacency_list.items():
        graph.add_node(node_id, node_data)
    
    # Add edges from edge list
    for edge_data in edge_list:
        graph.add_edge(edge_data)
    
    # Set initial input values for specified nodes
    for node_id, values in input_values.items():
        if node_id in graph.nodes:
            for key, value in values.items():
                graph.nodes[node_id].data_in[key] = value
    
    # Process graph
    graph.process_graph()
    
    # Return final graph state
    graph_state = graph.get_graph_state()
    return jsonify(graph_state), 200

if __name__ == "__main__":
    app.run(debug=True)
