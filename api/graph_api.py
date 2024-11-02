from flask import Flask, request, jsonify,Blueprint
from flask_mongoengine import MongoEngine
from typing import Dict, List, Union, Optional
from collections import defaultdict, deque
from dataclasses import dataclass
from models import *
from copy import deepcopy
from config import Config
import copy


graph_bp = Blueprint('graph', __name__)

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
        self.incoming_nodes: Dict[str, Node] = {}

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
    
    def detect_cycle(self) -> bool:
        """Detect if there's a cycle in the graph using DFS"""
        visited = set()
        rec_stack = set()

        def dfs_cycle(node_id: str) -> bool:
            visited.add(node_id)
            rec_stack.add(node_id)

            node = self.nodes[node_id]
            for edge in node.edges_out:
                neighbor = edge.dst_node
                if neighbor not in visited:
                    if dfs_cycle(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True

            rec_stack.remove(node_id)
            return False

        for node_id in self.nodes:
            if node_id not in visited:
                if dfs_cycle(node_id):
                    return True
        return False
    
    def check_connectivity(self) -> bool:
        """Check if graph is connected using DFS"""
        if not self.nodes:
            return True

        # Create an undirected version of the graph for connectivity check
        adjacency = defaultdict(set)
        for edge in self.edges:
            adjacency[edge.src_node].add(edge.dst_node)
            adjacency[edge.dst_node].add(edge.src_node)

        # Start DFS from any node
        start_node = next(iter(self.nodes))
        visited = set()

        def dfs_connect(node_id: str):
            visited.add(node_id)
            for neighbor in adjacency[node_id]:
                if neighbor not in visited:
                    dfs_connect(neighbor)

        dfs_connect(start_node)

        # Check if all nodes were visited
        return len(visited) == len(self.nodes)
    
    def get_priority_source(self, node: Node_1) -> List[str]:
        """Get source nodes in priority order (higher level first, then lexicographical)"""
        source_nodes = list(node.incoming_nodes.keys())
        sorted_nodes = sorted(source_nodes, key=lambda x: (-node.incoming_nodes[x].level, x))
        #print(f"\nPriority sources for {node.node_id}: {sorted_nodes}")  # Debug print
        return sorted_nodes
    
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
       
        """Process the graph using modified Kahn's algorithm with priority rules"""

        in_degree = defaultdict(int)
        for edge in self.edges:
            in_degree[edge.dst_node] += 1
        
        queue = deque()
        level_nodes = defaultdict(list)
        
        for node_id in self.nodes:
            if in_degree[node_id] == 0:
                queue.append(node_id)
                self.nodes[node_id].level = 0
                level_nodes[0].append(node_id)
        
        current_level = 0
        self.topological_order = []
        
        while queue:
            level_size = len(queue)
            for _ in range(level_size):
                current_node_id = queue.popleft()
                current_node = self.nodes[current_node_id]
                
                if current_node.visited:
                    continue
                
                current_node.visited = True
                self.topological_order.append(current_node_id)
                current_node.data_out = deepcopy(current_node.data_in)
                
                for edge in current_node.edges_out:
                    dst_node = self.nodes[edge.dst_node]
                    priority_sources = self.get_priority_source(dst_node)
                    
                    is_highest_priority = True
                    for higher_priority_src in priority_sources:
                        if higher_priority_src == current_node_id:
                            break
                        if self.nodes[higher_priority_src].visited:
                            is_highest_priority = False
                            break
                    if is_highest_priority:
                        for src_key, dst_key in edge.src_to_dst_data_keys.items():
                            if not dst_node.visited:
                                dst_node.data_in[dst_key] = deepcopy(current_node.data_out[src_key])
                    in_degree[edge.dst_node] -= 1
                    if in_degree[edge.dst_node] == 0:
                        queue.append(edge.dst_node)
                        dst_node.level = current_level + 1
                        level_nodes[current_level + 1].append(edge.dst_node)
            current_level += 1
        print("\nTopological Order:")
        for level in range(max(level_nodes.keys()) + 1):
            # Sort nodes of this level lexicographically
            nodes_at_level = sorted(level_nodes[level])
            if nodes_at_level:
                print(f"Level {level}: {' '.join(nodes_at_level)}")

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

@graph_bp.route('/process_graph', methods=['POST'])
def process_graph_endpoint():
    data = request.get_json()
    graph_id = data.get("graph_id")
    input_values = data.get("root_inputs", {})
    disabled_nodes=data.get("disable_list", [])
    data_overwrites=data.get("data_overwrites", {})
    edge_list=get_edges()
    edge_list = copy.deepcopy(edge_list)
    adjacency_list = get_graph(graph_id)
    adjacency_list = copy.deepcopy(adjacency_list)
    
    for node_key, new_data_in in data_overwrites.items():
        if node_key in adjacency_list:
            adjacency_list[node_key]["data_in"] = new_data_in
    
    for node, details in adjacency_list.items():
        for edge in details.get("edges", []):
            dst_node = edge.get("dst_node")
            # Check if the `dst_node` is in `data_overwrites` and update `data_in` accordingly
            if dst_node in data_overwrites:
                edge["data_in"] = data_overwrites[dst_node]
    
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
        
        connectivity=graph.check_connectivity()
        print("connectivity",connectivity)
        detect_cycle=graph.detect_cycle()
        print("detect_cycle",detect_cycle)
        if detect_cycle:
            return jsonify({"Result": "CYCLE DETECTED"}), 200
        if connectivity== False:
            return jsonify({"Result": "ISLANDS DETECTED"}), 200   
         
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
    graph_bp.run(debug=True)
