from flask import Flask, request, jsonify,Blueprint
from flask_mongoengine import MongoEngine
from typing import Dict, List, Set, Optional, Tuple,Union, Any
from collections import defaultdict, deque
from dataclasses import dataclass, field
from models import *
from copy import deepcopy
from config import Config
import copy


graph_bp = Blueprint('graph', __name__)

@graph_bp.route('/graph_run_config', methods=['POST'])
def process_graph_endpoint():
    data = request.get_json()
    graph_id = data.get("graph_id")
    input_values = data.get("root_inputs", {})
    disabled_nodes=data.get("disable_list", [])
    data_overwrites=data.get("data_overwrites", {})
    edge_list=get_edges()
    edge_list = copy.deepcopy(edge_list)
    # Fetch the adjacancy list from the graph_id from the nodes and edges saved in database
    adjacency_list = get_graph(graph_id)
    adjacency_list = copy.deepcopy(adjacency_list)
    
     # Overwrite the adjacency list as per the data_overwrites field of graph run config
    for node_key, new_data_in in data_overwrites.items():
        if node_key in adjacency_list:
            adjacency_list[node_key]["data_in"] = new_data_in
    
    for node, details in adjacency_list.items():
        for edge in details.get("edges", []):
            dst_node = edge.get("dst_node")
            # Check if the `dst_node` is in `data_overwrites` and update `data_in` accordingly
            if dst_node in data_overwrites:
                edge["data_in"] = data_overwrites[dst_node]
    
    # Remove the nodes and edges from adjacancy list as per the disabled_nodes field of graph run config
    for i in disabled_nodes:
        edge_list = [edge for edge in edge_list if edge["src_node"] != i]
        edge_list = [edge for edge in edge_list if edge["dst_node"] != i]
        for node, details in adjacency_list.items():
                details["edges"] = [edge for edge in details["edges"] if edge["dst_node"] != i]
        if i in adjacency_list:
            adjacency_list.pop(i)
    key = next(iter(input_values.keys()))
    
    # Check whether input_data given is on root node or not
    check_is_root_node = all(edge["dst_node"] != key for edge in edge_list)
    
    if check_is_root_node:
        graph = Graph_1()
        
        # Add node from adjacancy list
        for node_id, node_data in adjacency_list.items():
            graph.add_node(str(node_id), node_data)
            
        # Add edges from edge list
        for edge_data in edge_list:
            graph.add_edge(edge_data)
        
        # Check if there is more than one island in graph
        connectivity=graph.is_connected()
        if connectivity== False:
            return jsonify({"Result": "ISLANDS DETECTED"}), 200  
        
        # Check if there is cycle in graph 
        topo_order,cyclic=graph.process_graph()
        if cyclic==False:
            return jsonify({"Result": "CYCLE DETECTED"}), 200
    
         
        # Set initial input values for specified nodes
        for node_id, values in input_values.items():
            if node_id in graph.nodes:
                for key, value in values.items():
                    graph.set_node_data(node_id, key, value)
        
        # Run the transversal for making data transfer
        graph.propagate_data()
        
        # Get data_in and data_out at all the nodes
        all_nodes = graph.get_all_nodes()
        return jsonify({"Toposort":topo_order,
                        "Data":all_nodes}), 200
    else:
        return jsonify({"Result": "IT IS NOT A ROOT NODE"}), 200


# Type definitions
DataType = Union[int, str, bool, list, dict]

@dataclass
class Edge_1:
    """Represents an edge in the graph with its properties."""
    edge_id: str
    src_node: str
    dst_node: str
    src_to_dst_data_keys: Dict[str, str]

@dataclass
class Node_1:
    """Represents a node in the graph with its properties."""
    node_id: str
    data_in: Dict[str, str] = field(default_factory=dict)
    data_out: Dict[str, str] = field(default_factory=dict)
    runtime_data: Dict[str, Any] = field(default_factory=dict)

class Graph_1:
    """A directed graph implementation with support for topological sorting and data flow."""
    
    def __init__(self):
        self.nodes: Dict[str, Node_1] = {}
        self.edges: Dict[str, Edge_1] = {}
        self.directed_adj: Dict[str, List[str]] = defaultdict(list)
        self.undirected_adj: Dict[str, List[str]] = defaultdict(list)
        self.indegree: Dict[str, int] = defaultdict(int)
        self.dependent_on: Dict[str, str] = {}

    def add_node(self, node_id: str, node_data: dict) -> bool:
        """
        Add a new node to the graph.
        Returns True if successful, False if node already exists.
        """
        if node_id in self.nodes:
            return False
        
        node = Node_1(
            node_id=node_id,
            data_in=node_data.get('data_in', {}),
            data_out=node_data.get('data_out', {})
        )
        self.nodes[node_id] = node
        return True

    

    def add_edge(self, edge_data: dict) -> bool:
        """
        Add a new edge to the graph.
        Returns True if successful, False if edge already exists or nodes don't exist.
        """
        edge_id = edge_data['edge_id']
        src_node = edge_data['src_node']
        dst_node = edge_data['dst_node']
        
        if (edge_id in self.edges or 
            src_node not in self.nodes or 
            dst_node not in self.nodes):
            return False

        edge = Edge_1(
            edge_id=edge_id,
            src_node=src_node,
            dst_node=dst_node,
            src_to_dst_data_keys=edge_data['src_to_dst_data_keys']
        )
        
        self.edges[edge_id] = edge
        self.directed_adj[src_node].append(dst_node)
        self.undirected_adj[src_node].append(dst_node)
        self.undirected_adj[dst_node].append(src_node)
        self.indegree[dst_node] += 1
        
        return True


    def is_connected(self) -> bool:
        """Check if the graph is connected."""
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
    
    def get_all_nodes(self) -> Dict[str, Node_1]:
        """Returns all nodes as Node objects."""
        updated_nodes = {}
        
        for node_id, node in self.nodes.items():
            # Update data_in and data_out with values from runtime_data, setting unmatched keys to None
            for key in node.data_in:
                node.data_in[key] = node.runtime_data.get(key, None)
            for key in node.data_out:
                node.data_out[key] = node.runtime_data.get(key, None)
            
            # Remove runtime_data from the node
            updated_nodes[node_id] = {
                "data_in": node.data_in,
                "data_out": node.data_out
            }
        
        return updated_nodes
    
    def propagate_data(self):
        """Propagate data from each node's data_out to the data_in of downstream nodes."""
        topo_order, is_not_cyclic = self.process_graph()
        if not is_not_cyclic:
            print("Error: Cycle detected")
            return False
        
        # Perform data propagation
        for level in topo_order:
            for node_id in level:
                node = self.nodes[node_id]
                
                # Propagate data_out to connected nodes' data_in
                for dst_node_id in self.directed_adj[node_id]:
                    dst_node = self.nodes[dst_node_id]
                    edge = next(
                        (e for e in self.edges.values() if e.src_node == node_id and e.dst_node == dst_node_id),
                        None
                    )
                    if edge:
                        for src_key, dst_key in edge.src_to_dst_data_keys.items():
                            if src_key in node.runtime_data:
                                value = node.runtime_data[src_key]
                                dst_node.data_in[dst_key] = value
                                dst_node.runtime_data[dst_key] = value
                                dst_node.data_out[dst_key] = value
    def process_graph(self) -> Tuple[List[List[str]], bool]:
        """
        Process the graph to get topological ordering and check for cycles.
        Returns (topological_order, is_not_cyclic).
        """
        topo_order = []
        is_not_cyclic = True
        indegree_copy = deepcopy(self.indegree)
        
        current_nodes = [
            node_id for node_id in self.nodes 
            if indegree_copy[node_id] == 0
        ]
        
        while current_nodes:
            current_level_nodes = []
            future_nodes = []
            
            current_nodes.sort()  # Lexicographical ordering
            
            while current_nodes:
                current_node = current_nodes.pop()
                current_level_nodes.append(current_node)
            
                for neighbor in self.directed_adj[current_node]:
                    indegree_copy[neighbor] -= 1
                    if indegree_copy[neighbor] == 0:
                        self.dependent_on[neighbor] = current_node
                        future_nodes.append(neighbor)
            
            topo_order.append(current_level_nodes)
            current_nodes.extend(sorted(future_nodes))
                
        # Check for cycles
        is_not_cyclic = all(indegree_copy[node_id] == 0 for node_id in self.nodes)
                
        return topo_order, is_not_cyclic
    

    def set_node_data(self, node_id: str, data_key: str, value: Any) -> bool:
        """Set runtime data for a node."""
        if node_id not in self.nodes:
            return False
        self.nodes[node_id].runtime_data[data_key] = value
        return True
    

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


    


if __name__ == "__main__":
    graph_bp.run(debug=True)
