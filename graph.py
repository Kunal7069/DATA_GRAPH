from typing import Dict, List, Union, Optional
from collections import defaultdict, deque
from dataclasses import dataclass
from copy import deepcopy
import json

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
        self.data_in = {}  # Will store actual values
        self.data_out = {}  # Will store actual values
        self.data_in_types = data_in  # Store type information
        self.data_out_types = data_out  # Store type information
        self.level = -1
        self.visited = False
        self.edges_out: List[Edge] = []

class Graph:
    def __init__(self):
        self.nodes: Dict[str, Node] = {}
        self.edges: List[Edge] = []
    
    def add_node(self, node_id: str, node_data: dict) -> None:
        """Add a node to the graph from the adjacency list format"""
        # Ensure data_out contains all keys from data_in
        data_out = node_data.get("data_out", {})
        # Copy all data_in types to data_out if not already present
        for key, type_str in node_data["data_in"].items():
            if key not in data_out:
                data_out[key] = type_str
                
        node = Node(
            node_id=node_id,
            data_in=node_data["data_in"],
            data_out=data_out
        )
        self.nodes[node_id] = node
        
        # Initialize both data_in and data_out with default values
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
        """Add an edge to the graph from the edge list format"""
        edge = Edge(
            edge_id=edge_data["edge_id"],
            src_node=edge_data["src_node"],
            dst_node=edge_data["dst_node"],
            src_to_dst_data_keys=edge_data["src_to_dst_data_keys"]
        )
        self.edges.append(edge)
        self.nodes[edge.src_node].edges_out.append(edge)
    
    def process_graph(self) -> None:
        """Process the graph using Kahn's algorithm"""
        # Calculate in-degrees
        in_degree = defaultdict(int)
        for edge in self.edges:
            in_degree[edge.dst_node] += 1
        
        # Initialize queue with roots (nodes with in-degree 0)
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
                
                # Copy data_in to data_out for processing
                current_node.data_out = deepcopy(current_node.data_in)
                
                # Process outgoing edges
                for edge in current_node.edges_out:
                    dst_node = self.nodes[edge.dst_node]
                    
                    # Transfer data according to mappings
                    for src_key, dst_key in edge.src_to_dst_data_keys.items():
                        if not dst_node.visited:  # Only update if destination hasn't been visited
                            dst_node.data_in[dst_key] = deepcopy(current_node.data_out[src_key])
                    
                    # Update in-degree and queue
                    in_degree[edge.dst_node] -= 1
                    if in_degree[edge.dst_node] == 0:
                        queue.append(edge.dst_node)
                        dst_node.level = current_level + 1
            
            current_level += 1

    def print_graph_state(self, title: str = "") -> None:
        """Print the current state of the graph"""
        print(f"\n{title}")
        print("=" * len(title))
        for node_id, node in sorted(self.nodes.items()):
            print(f"\nNode: {node_id} (Level: {node.level}, Visited: {node.visited})")
            print("Data In:")
            for key, value in sorted(node.data_in.items()):
                print(f"  {key}: {value} ({node.data_in_types[key]})")
            print("Data Out:")
            for key, value in sorted(node.data_out.items()):
                print(f"  {key}: {value} ({node.data_out_types[key]})")

def run_test_case():
    # Test case data
    adjacency_list = {
        "node1": {
            "data_in": {
                "input_key1": "int",
                "input_key2": "int",
                "input_key3": "int"
            },
            "data_out": {
                "input_key2": "int",
                "input_key3": "int"
            },
            "edges": [
                {
                    "data_in": {
                        "input_key4": "int",
                        "input_key5": "int"
                    },
                    "data_out": {
                        "input_key4": "int",
                        "input_key5": "int"
                    },
                    "dst_node": "node2"
                },
                {
                     "data_in": {
                        "input_key6": "int",
                        "input_key7": "int"
                    },
                    "data_out": {
                        "input_key6": "int",
                        "input_key7": "int"
                    },
                    "dst_node": "node3"
                }
            ]
        },
        "node2": {
            "data_in": {
                "input_key4": "int",
                "input_key5": "int"
            },
            "data_out": {
                "input_key4": "int",
                "input_key5": "int"
            },
            "edges": [
                 {
                     "data_in": {
                        "input_key10": "int",
                    },
                    "data_out": {
                        "input_key10": "int",
                    },
                    "dst_node": "node5"
                }
            ]
        },
        "node3": {
            "data_in": {
                "input_key6": "int",
                "input_key7": "int"
            },
            "data_out": {
                "input_key6": "int",
                "input_key7": "int"
            },
            "edges": [
                 {
                     "data_in": {
                        "input_key8": "int",
                        "input_key9": "int"
                    },
                    "data_out": {
                        "input_key8": "int",
                        "input_key9": "int"
                    },
                    "dst_node": "node4"
                }
            ]
        },
        "node4": {
            "data_in": {
                "input_key8": "int",
                "input_key9": "int"
            },
            "data_out": {
                "input_key8": "int",
                "input_key9": "int"
            },
            "edges": [
                 {
                     "data_in": {
                        "input_key10": "int",
                    },
                    "data_out": {
                        "input_key10": "int"
                    },
                    "dst_node": "node5"
                }
            ]
        },
        "node5": {
            "data_in": {
                "input_key10": "int"
            },
            "data_out": {
               "input_key10": "int",
            },
            "edges": []
        }
}

    edge_list = [
        
        {
            "dst_node": "node5",
            "edge_id": "edge3",
            "src_node": "node2",
            "src_to_dst_data_keys": {
                "input_key5": "input_key10"
            }
        },
        {
            "dst_node": "node4",
            "edge_id": "edge4",
            "src_node": "node3",
            "src_to_dst_data_keys": {
                "input_key6": "input_key8",
                "input_key7": "input_key9"
            }
        },
        {
            "dst_node": "node5",
            "edge_id": "edge5",
            "src_node": "node4",
            "src_to_dst_data_keys": {
                "input_key9": "input_key10"
            }
        }]
    
    
    graph = Graph()
    
    # Add nodes from adjacency list
    for node_id, node_data in adjacency_list.items():
        graph.add_node(node_id, node_data)
    
    # Add edges from edge list
    for edge_data in edge_list:
        graph.add_edge(edge_data)
    
    # Set some initial values for node1
    graph.nodes["node2"].data_in["input_key4"] = 2
    graph.nodes["node2"].data_in["input_key5"] = 3
    # graph.nodes["node1"].data_in["input_key3"] = 4
    
    
    # Print initial state
    graph.print_graph_state("Initial State")
    
    # Process graph
    graph.process_graph()
    
    # Print final state
    graph.print_graph_state("After Processing")


run_test_case()