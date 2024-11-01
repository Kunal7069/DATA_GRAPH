from flask import Blueprint, jsonify, request
from models import Node, Edge

crud_bp = Blueprint('crud', __name__)


@crud_bp.route('/create_nodes', methods=['POST'])
def create_node():
    data = request.json
    required_fields = ['node_id', 'data_in', 'data_out']
    
    # Check for required fields
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing required field: {field}"}), 400
    
    # Data type validation mapping
    type_mapping = {
        "int": int,
        "float": float,
        "str": str,
        "bool": bool,
        "list": list,
        "dict": dict
    }
    
    data_in = data['data_in']
    data_out = data['data_out']
    
    # Check if all keys in data_out are present in data_in
    for key in data_out.keys():
        if key not in data_in:
            return jsonify({
                "error": f"Key '{key}' in data_out is not present in data_in"
            }), 400

    
    # Check if data types for the same keys in data_in and data_out match
    for key, expected_type_str in data_in.items():
        if key in data_out:
            expected_type = type_mapping.get(expected_type_str)
            actual_type = type_mapping.get(data_out[key])
            
            if expected_type is None or actual_type is None:
                return jsonify({
                    "error": f"Invalid type for key '{key}'"
                }), 400
            
            if expected_type != actual_type:
                return jsonify({
                    "error": f"Data type mismatch for key '{key}': "
                             f"{expected_type_str} in data_in vs {data_out[key]} in data_out"
                }), 400

    try:
        # Create and save a new Node object if validation passes
        new_node = Node(
            node_id=data['node_id'],
            data_in=data_in,
            data_out=data_out,
            paths_in=[],  # Assuming paths_in and paths_out are initially empty
            paths_out=[]
        )
        new_node.save()  # Save the node to the database
        return jsonify({"message": "Node created successfully", "node_id": new_node.node_id}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500  # Handle errors during save


@crud_bp.route('/create_edges', methods=['POST'])
def create_edge():
    data = request.json
    required_fields = ['edge_id', 'src_node', 'dst_node', 'src_to_dst_data_keys']
    
    # Check for required fields
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing required field: {field}"}), 400
    
    src_node_id = data['src_node']
    dst_node_id = data['dst_node']
    src_to_dst_data_keys = data['src_to_dst_data_keys']

    # Fetch source and destination nodes
    src_node = Node.objects(node_id=src_node_id).first()
    dst_node = Node.objects(node_id=dst_node_id).first()

    if not src_node or not dst_node:
        return jsonify({"error": "Source or destination node does not exist"}), 404

    # Validate that the keys in src_to_dst_data_keys match the data types
    for src_key, dst_key in src_to_dst_data_keys.items():
        if src_key not in src_node.data_out or dst_key not in dst_node.data_in:
            return jsonify({"error": f"Key '{src_key}' not found in src_node data_out or "
                                       f"key '{dst_key}' not found in dst_node data_in"}), 400
        
        # Get actual data types of the values
        src_value_type = src_node.data_out[src_key]
        dst_value_type = dst_node.data_in[dst_key]
    
        # Check if types match
        if src_value_type != dst_value_type:
            return jsonify({
                "error": f"Data type mismatch for key '{src_key}': "
                         f"{src_value_type} vs {dst_value_type}"
            }), 400

    try:
        # Create a new Edge object
        new_edge = Edge(
            edge_id=data['edge_id'],
            src_node=src_node_id,
            dst_node=dst_node_id,
            src_to_dst_data_keys=src_to_dst_data_keys
        )
        new_edge.save()  # Save the edge to the database

        # Update the paths of the nodes
        src_node.paths_out.append(new_edge)  # Add edge to src_node's outgoing paths
        dst_node.paths_in.append(new_edge)    # Add edge to dst_node's incoming paths
        src_node.save()  # Save the updated src_node
        dst_node.save()  # Save the updated dst_node

        return jsonify({"message": "Edge created successfully", "edge_id": new_edge.edge_id}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500  # Handle errors during save


@crud_bp.route('/create_graph', methods=['POST'])
def create_graph():
    data = request.json
    
    if 'nodes' not in data:
        return jsonify({"error": "Missing required field: nodes"}), 400

    node_ids = data['nodes']
    graph_id = data['graph_id']

    # Validate that all nodes exist
    nodes = []
    for node_id in node_ids:
        node = Node.objects(node_id=node_id).first()
        if not node:
            return jsonify({"error": f"Node with id '{node_id}' does not exist"}), 404
        nodes.append(node['node_id'])

    try:
        # Create a new Graph object
        new_graph = Graph(graph_id=graph_id,nodes=nodes)
        new_graph.save()  # Save the graph to the database

        return jsonify({"message": "Graph created successfully", "graph_id": str(new_graph.id)}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500  # Handle errors during save

@crud_bp.route('/get_graph', methods=['POST'])
def get_graph():
    data = request.json
    graph_id = data.get("graph_id")

    if not graph_id:
        return jsonify({"error": "Missing graph_id in request body"}), 400

    # Fetch the graph by graph_id
    graph = Graph.objects(graph_id=graph_id).first()
    
    if not graph:
        return jsonify({"error": "Graph not found"}), 404

    # Construct the adjacency list
    adjacency_list = {}
    print(graph['graph_id'])
    for node_ref in graph.nodes:
        # Dereference the node reference to get the actual Node document
        node = Node.objects(node_id=node_ref.id).first() 
        print(node['node_id'])
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

    return jsonify(adjacency_list), 200

@crud_bp.route('/get_edges', methods=['GET'])
def get_edges():
    # Fetch all edges from the database
    edges = Edge.objects()  # Retrieve all Edge documents

    # Format the edges as a list of dictionaries to return as JSON
    edges_list = []
    for edge in edges:
        edges_list.append({
            "edge_id": edge.edge_id,
            "src_node": edge.src_node,
            "dst_node": edge.dst_node,
            "src_to_dst_data_keys": edge.src_to_dst_data_keys
        })

    return jsonify(edges_list), 200


@crud_bp.route('/', methods=['GET'])
def home():
    return jsonify({"message": "CRUD API IS RUNNING"}), 201


if __name__ == '__main__':
    crud_bp.run(debug=True)
