import networkx as nx

NODE_COLOR_MAP = {
    "module": "purple",
    "class_definition": "darkgreen",
    "function_definition": "green",
    "identifier": "orange",
    "string": "darkorange",
    "integer": "darkorange",
    "float": "darkorange",
    "call": "yellow",
}
NODE_SHAPE_MAP = {
    "module": "box3d",
    "class_definition": "component",
    "function_definition": "component",
    "if_statement": "diamond",
    "elif_clause": "diamond",
    "else_clause": "diamond",
    "identifier": "box",
    "string": "box",
    "integer": "box",
    "float": "box",
    "call": "ellipse",
}

NODE_SHAPE_MAP_BY_FIELD = {
    "condition": "Mdiamond",
}

EDGE_COLOR_MAP = {
    "CF": "red",
    "DF": "blue",
}
    
def render(G: nx.MultiDiGraph, output_path: str):
    A = nx.nx_agraph.to_agraph(G)
    
    # Add node and edge data to label
    for node in G.nodes:
        n = A.get_node(node)
        
        node_data = G.nodes[node]
        label = create_label(node_data)
        n.attr['label'] = label
        
        node_type = node_data.get('type', 'default')
        n.attr['color'] = NODE_COLOR_MAP.get(node_type, 'gray')
        n.attr['shape'] = NODE_SHAPE_MAP.get(node_type, 'ellipse')
        
        node_field = node_data.get('field_name', 'default')
        n.attr['shape'] = NODE_SHAPE_MAP_BY_FIELD.get(node_field, n.attr['shape'])
    
    for edge in G.edges:
        e = A.get_edge(edge[0], edge[1])
        e.attr['label'] = edge[2]
        edge_color = EDGE_COLOR_MAP.get(edge[2], 'black')
        e.attr['color'] = edge_color
    
    # Draw the graph to a file and display
    A.draw(output_path, prog='dot')

LABEL_TOGGLE = {
    "type": True,
    "field_name": True,
    "text": True,
    "src_bytes_range": False,
    "start_point": False,
    "end_point": False,
    "path": True,
    "module": False,
}

def create_label(data):
    return '\n'.join([f"{k}: {v}" for k, v in data.items() if LABEL_TOGGLE.get(k, True)])