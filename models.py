# models.py

from mongoengine import Document, StringField, ListField, ReferenceField, MapField, DynamicField

# Define the compatible DataType types for MongoDB (int, float, str, bool, list, dict)
DataType = DynamicField()  # Allows any data type

### Edge Model ###
class Edge(Document):
    edge_id = StringField(required=True, unique=True)
    src_node = StringField(required=True)
    dst_node = StringField(required=True)
    src_to_dst_data_keys = MapField(StringField())  # Maps `str` keys to `str` values

    meta = {'collection': 'edges'}  


### Node Model ###
class Node(Document):
    node_id = StringField(required=True, unique=True)
    data_in = MapField(DataType)  # Maps `str` keys to any DataType as value
    data_out = MapField(DataType)  # Maps `str` keys to any DataType as value
    paths_in = ListField(ReferenceField(Edge))  # List of incoming edges
    paths_out = ListField(ReferenceField(Edge))  # List of outgoing edges

    meta = {'collection': 'nodes'}  # MongoDB collection name


### Graph Model ###
class Graph(Document):
    graph_id = StringField(required=True, unique=True)
    nodes = ListField(ReferenceField(Node))  # List of Node references
    
    meta = {'collection': 'graphs'}  # MongoDB collection name


### GraphRunConfig Model ###
class GraphRunConfig(Document):
    root_inputs = MapField(MapField(DataType))  # Dict[str, Dict[str, DataType]]
    data_overwrites = MapField(MapField(DataType))  # Dict[str, Dict[str, DataType]]
    enable_list = ListField(StringField())  # List of enabled node_ids
    disable_list = ListField(StringField())  # List of disabled node_ids

    meta = {'collection': 'graph_run_configs'}  # MongoDB collection name
