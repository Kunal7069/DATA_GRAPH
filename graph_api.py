from flask import Flask, request, jsonify
from flask_mongoengine import MongoEngine
from typing import Dict, List, Union, Optional
from collections import defaultdict, deque
from dataclasses import dataclass
from models import *
from copy import deepcopy
from config import Config
import copy

# Initialize Flask app and load configuration
app = Flask(__name__)

app.config["MONGODB_SETTINGS"] = {
    "host": Config.MONGO_URI
}
db = MongoEngine(app)

# Check the connection by pinging the database within the application context
with app.app_context():
    try:
        db.connection.admin.command('ping')
        print("Connected to MongoDB!")
    except Exception as e:
        print("Failed to connect to MongoDB:", e)
# Type definitions
DataType = Union[int, str, bool, list, dict]

@dataclass
class Edge_1:
    edge_id: str
    src_node: str
    dst_node: str
    src_to_dst_data_keys: Dict[str, str]

class Node_1:
    def __init__(self, node_id: str, data_in: Dict[str, str], data_out: Dict[str, str]):
        self.node_id = node_id
        self.data_in = {}
        self.data_out = {}
        self.data_in_types = data_in
        self.data_out_types = data_out
        self.level = -1
        self.visited = False
        self.edges_out: List[Edge_1] = []

class Graph_1:
    def __init__(self):
        self.nodes: Dict[str, Node_1] = {}
        self.edges: List[Edge_1] = []
    
    def add_node(self, node_id: str, node_data: dict) -> None:
        data_out = node_data.get("data_out", {})
        for key, type_str in node_data["data_in"].items():
            if key not in data_out:
                data_out[key] = type_str
                
        node = Node_1(
            node_id=node_id,
            data_in=node_data["data_in"],
            data_out=data_out
        )
        self.nodes[node_id] = node
        for dictionary in [node.data_in, node.data_out]:
            for key, type_str in node_data["data_in"].items():
                if type_str == "int":
                    dictionary[key] = 'Null'
                elif type_str == "str":
                    dictionary[key] = ""
                elif type_str == "bool":
                    dictionary[key] = 'Null'
                elif type_str == "list":
                    dictionary[key] = []
                elif type_str == "dict":
                    dictionary[key] = {}
    
    def add_edge(self, edge_data: dict) -> None:
        edge = Edge_1(
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

def get_edges():
    edges = Edge.objects()  
    edges_list = []
    for edge in edges:
        edges_list.append({
            "dst_node": edge.dst_node,
            "edge_id": edge.edge_id,
            "src_node": edge.src_node,
            "src_to_dst_data_keys": edge.src_to_dst_data_keys
        })

    return(edges_list)


def get_graph(graph_id):

    if not graph_id:
        return jsonify({"error": "Missing graph_id in request body"}), 400

    # Fetch the graph by graph_id
    graph = Graph.objects(graph_id=graph_id).first()
    
    if not graph:
        return jsonify({"error": "Graph not found"}), 404

    # Construct the adjacency list
    adjacency_list = {}
    for node_ref in graph.nodes:
        # Dereference the node reference to get the actual Node document
        node = Node.objects(node_id=node_ref.id).first() 
        # For each node, get its data_in and data_out
        adjacency_list[node['node_id']] = {
            "data_in": node.data_in,
            "data_out": node.data_out,
            "edges": []  # Initialize empty list for edges
        }

        # # Collect outgoing edges to build the adjacency representation
        for edge in node.paths_out:
            # Fetch the destination node object
            dst_node = Node.objects(node_id=edge.dst_node).first()
            if dst_node:
                # Add the destination node and its data_in and data_out
                adjacency_list[node.node_id]["edges"].append({
                    "data_out": dst_node.data_out,
                    "data_in": dst_node.data_in,
                    "dst_node": edge.dst_node,
                })

    return (adjacency_list)

@app.route('/process_graph', methods=['POST'])
def process_graph_endpoint():
    data = request.get_json()
    graph_id = data.get("graph_id")
    input_values = data.get("input_values", {})
    disabled_nodes=data.get("disabled_nodes", [])
    edge_list=get_edges()
    edge_list = copy.deepcopy(edge_list)
    adjacency_list = get_graph(graph_id)
    adjacency_list = copy.deepcopy(adjacency_list)
    for i in disabled_nodes:
        edge_list = [edge for edge in edge_list if edge["src_node"] != i]
        edge_list = [edge for edge in edge_list if edge["dst_node"] != i]
        for node, details in adjacency_list.items():
                details["edges"] = [edge for edge in details["edges"] if edge["dst_node"] != i]
        if i in adjacency_list:
            adjacency_list.pop(i)
    key = next(iter(input_values.keys()))
    check_is_root_node = all(edge["dst_node"] != key for edge in edge_list)
    if check_is_root_node:
        graph = Graph_1()
        
        for node_id, node_data in adjacency_list.items():
            graph.add_node(str(node_id), node_data)
            
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
    else:
        return jsonify({"Result": "IT IS NOT A ROOT NODE"}), 200


if __name__ == "__main__":
    app.run(debug=True)
