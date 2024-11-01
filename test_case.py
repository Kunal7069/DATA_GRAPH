adjacency_list = {
      
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
        "dst_node": "node5",
        "edge_id": "edge5",
        "src_node": "node4",
        "src_to_dst_data_keys": {
            "input_key9": "input_key10"
        }
    }]
    
graph.nodes["node2"].data_in["input_key4"] = 2
graph.nodes["node2"].data_in["input_key5"] = 3