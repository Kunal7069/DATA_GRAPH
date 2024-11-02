from typing import Dict, List, Union, Set
from collections import defaultdict, deque
from dataclasses import dataclass
from copy import deepcopy

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
        self.incoming_nodes: Dict[str, Node] = {}  # Track nodes that affect this node

class Graph:
    def __init__(self):
        self.nodes: Dict[str, Node] = {}
        self.edges: List[Edge] = []
        self.topological_order: List[str] = []
    
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

    def get_priority_source(self, node: Node) -> List[str]:
        """Get source nodes in priority order (higher level first, then lexicographical)"""
        source_nodes = list(node.incoming_nodes.keys())
        sorted_nodes = sorted(source_nodes, key=lambda x: (-node.incoming_nodes[x].level, x))
        #print(f"\nPriority sources for {node.node_id}: {sorted_nodes}")  # Debug print
        return sorted_nodes

    def process_graph(self) -> None:
        """Process the graph using modified Kahn's algorithm with priority rules"""
        # First check for cycles
        if self.detect_cycle():
            print("\nCycle detected")
            return

        # Check connectivity
        if not self.check_connectivity():
            print("\nGraph not connected")
        else:
            print("\nGraph connected")

        # Calculate in-degrees
        in_degree = defaultdict(int)
        for edge in self.edges:
            in_degree[edge.dst_node] += 1
        
        queue = deque()
        level_nodes = defaultdict(list)

        # Initialize queue with roots
        for node_id in self.nodes:
            if in_degree[node_id] == 0:
                queue.append(node_id)
                self.nodes[node_id].level = 0
                level_nodes[0].append(node_id)
                #print(f"Root node found: {node_id}")  # Debug print
        
        current_level = 0
        self.topological_order = []
        
        while queue:
            level_size = len(queue)
            #print(f"\nProcessing level {current_level}")  # Debug print
            
            for _ in range(level_size):
                current_node_id = queue.popleft()
                current_node = self.nodes[current_node_id]
                
                if current_node.visited:
                    continue
                
                current_node.visited = True
                self.topological_order.append(current_node_id)
                #print(f"\nProcessing node: {current_node_id}")  # Debug print
                
                # Copy data_in to data_out for processing
                current_node.data_out = deepcopy(current_node.data_in)
                
                # Process outgoing edges
                for edge in current_node.edges_out:
                    dst_node = self.nodes[edge.dst_node]
                    #print(f"  Examining edge to {edge.dst_node}")  # Debug print
                    
                    # Get priority source for the destination node
                    priority_sources = self.get_priority_source(dst_node)
                    
                    # Check priority
                    is_highest_priority = True
                    for higher_priority_src in priority_sources:
                        if higher_priority_src == current_node_id:
                            break
                        if self.nodes[higher_priority_src].visited:
                            is_highest_priority = False
                            break
                    
                    #print(f"  Is highest priority: {is_highest_priority}")  # Debug print
                    
                    # Transfer data according to mappings if highest priority
                    if is_highest_priority:
                        for src_key, dst_key in edge.src_to_dst_data_keys.items():
                            dst_node.data_in[dst_key] = deepcopy(current_node.data_out[src_key])
                            #print(f"  Transferring {src_key}={current_node.data_out[src_key]} to {dst_key}")  # Debug print
                    
                    # Update in-degree and queue
                    in_degree[edge.dst_node] -= 1
                    if in_degree[edge.dst_node] == 0:
                        queue.append(edge.dst_node)
                        dst_node.level = current_level + 1
                        level_nodes[current_level + 1].append(edge.dst_node)
            
            current_level += 1

        # Print topological order by level
        print("\nTopological Order:")
        for level in range(max(level_nodes.keys()) + 1):
            # Sort nodes of this level lexicographically
            nodes_at_level = sorted(level_nodes[level])
            if nodes_at_level:
                print(f"Level {level}: {' '.join(nodes_at_level)}")

    def add_node(self, node_id: str, node_data: dict) -> None:
        """Add a node to the graph"""
        # Create node with type information
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
        
        # Initialize data_in with default values
        for key, type_str in node_data["data_in"].items():
            if type_str == "int":
                node.data_in[key] = 0
            elif type_str == "str":
                node.data_in[key] = ""
            elif type_str == "bool":
                node.data_in[key] = False
            elif type_str == "list":
                node.data_in[key] = []
            elif type_str == "dict":
                node.data_in[key] = {}
        
        # Initialize data_out with same values as data_in
        node.data_out = deepcopy(node.data_in)
    
    def add_edge(self, edge_data: dict) -> None:
        """Add an edge to the graph"""
        edge = Edge(
            edge_id=edge_data["edge_id"],
            src_node=edge_data["src_node"],
            dst_node=edge_data["dst_node"],
            src_to_dst_data_keys=edge_data["src_to_dst_data_keys"]
        )
        self.edges.append(edge)
        self.nodes[edge.src_node].edges_out.append(edge)
        self.nodes[edge.dst_node].incoming_nodes[edge.src_node] = self.nodes[edge.src_node]

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
        "node2": {
            "data_in": {
                "input_key4": "int",
                "input_key5": "int"
            },
            "data_out": {
                "input_key4": "int",
                "input_key5": "int"
            }
        },
        "node4": {
            "data_in": {
                "input_key8": "int",
                "input_key9": "int"
            },
            "data_out": {
                "input_key8": "int",
                "input_key9": "int"
            }
        },
        "node5": {
            "data_in": {
                "input_key10": "int"
            },
            "data_out": {
                "input_key10": "int"
            }
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
            "dst_node": "node5",
            "edge_id": "edge5",
            "src_node": "node4",
            "src_to_dst_data_keys": {
                "input_key9": "input_key10"
            }
        }
    ]

    # Create and populate graph
    graph = Graph()
    
    # Add nodes and edges
    for node_id, node_data in adjacency_list.items():
        graph.add_node(node_id, node_data)
    
    for edge_data in edge_list:
        graph.add_edge(edge_data)
    
    # Set initial values
    graph.nodes["node2"].data_in["input_key4"] = 2
    graph.nodes["node2"].data_in["input_key5"] = 3
    # Copy to data_out
    graph.nodes["node2"].data_out = deepcopy(graph.nodes["node2"].data_in)
    
    graph.nodes["node4"].data_in["input_key8"] = 8
    graph.nodes["node4"].data_in["input_key9"] = 9
    # Copy to data_out
    graph.nodes["node4"].data_out = deepcopy(graph.nodes["node4"].data_in)
    
    # Print initial state
    graph.print_graph_state("Initial State")
    
    # Process graph
    graph.process_graph()
    
    # Print final state
    graph.print_graph_state("After Processing")

if _name_ == "_main_":
    run_test_case()