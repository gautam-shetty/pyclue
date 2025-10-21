from tree_sitter import Parser, Tree, Node

from constants import TSLanguage, TSNodeGroup, DummyNode, EdgeType, TypePairs
import utils

class AbstractSyntaxTree:
    def __init__(self, repo_path, file_path):
        self.repo_path = repo_path
        self.path = file_path
        self.parser = Parser(TSLanguage.PY_LANGUAGE)
        self.src_bytes = utils.get_file_bytes(".py", self.path)
        self.tree: Tree = self.parse()
        
    def _read_callable_byte_offset(self, byte_offset, point):
        return self.src_bytes[byte_offset : byte_offset + 1]

    def parse(self):
        return self.parser.parse(self._read_callable_byte_offset, encoding="utf8")
        
    def generate_nodes_and_edges(self, node: Node, parent=None):
        """
        Recursively traverses Tree-sitter syntax tree and adds to NetworkX graph.
        Uses the node's start_byte as the unique identifier.
        """
        nodes = []
        edges = []
        
        current_node_id = self.generate_node_unique_id(node)
        
        # Add the current node with its type as an attribute
        node_props = self.get_node_properties(node)
        if node_props is None:
            return [], []
        else:
            nodes.append((current_node_id, node_props))
        
        # Add a dummy node for required node types
        if node.type in TSNodeGroup.NODES_WITH_DUMMY_NODE:
            if node.type in [TSNodeGroup.MODULE, TSNodeGroup.CLS_NODE]:
                dummy_A = self.generate_node_unique_id(node, DummyNode.START)
                nodes.append((dummy_A, self.generate_dummy_node(node, DummyNode.START)))
                edges.append((current_node_id, dummy_A, EdgeType.AST))
                dummy_B = self.generate_node_unique_id(node, DummyNode.EXIT)
                nodes.append((dummy_B, self.generate_dummy_node(node, DummyNode.EXIT)))
                edges.append((current_node_id, dummy_B, EdgeType.AST))
            elif node.type == TSNodeGroup.FN_NODE:
                dummy_A = self.generate_node_unique_id(node, DummyNode.ENTRY)
                nodes.append((dummy_A, self.generate_dummy_node(node, DummyNode.ENTRY)))
                edges.append((current_node_id, dummy_A, EdgeType.AST))
                dummy_B = self.generate_node_unique_id(node, DummyNode.RETURN)
                nodes.append((dummy_B, self.generate_dummy_node(node, DummyNode.RETURN)))
                edges.append((current_node_id, dummy_B, EdgeType.AST))
        
        if parent is not None:
            # Add an edge from the parent node to the current node
            edges.append((parent, current_node_id, EdgeType.AST))
        
        # Traverse child nodes recursively
        for child in node.children:
            child_nodes, child_edges = self.generate_nodes_and_edges(child, current_node_id)
            
            # Accumulate nodes and edges from the child
            nodes.extend(child_nodes)
            edges.extend(child_edges)
            
        return nodes, edges
    
    def generate_node_unique_id(self, node: Node, dummy_str=None):
        """
        Generates a unique identifier for a node based on its file relative path, type, start_byte, and end_byte.
        """
        rel_path = utils.get_relative_path(self.path, self.repo_path)
        string_to_hash = f"{rel_path}.{node.type}.{node.start_byte}.{node.end_byte}"
        if dummy_str:
            string_to_hash += f".{dummy_str}"
        
        return utils.generate_uuid(string_to_hash)
    
    def get_node_properties(self, node: Node):
        """
        Extracts the properties of a tree-sitter node for the graph.
        """
        node_type = node.type
        
        # Skip nodes that are in the skip_nodes list
        if node_type in TSNodeGroup.SKIP_NODES_BY_TYPE:
            return None
        
        props = {
            "type": node_type,
            "field_name": None,
            "text": None,
            "src_bytes_range": (node.start_byte, node.end_byte),
            "start_point": (node.start_point.row, node.start_point.column),
            "end_point": (node.end_point.row, node.end_point.column),
            "module": utils.get_relative_path(self.path, self.repo_path)
        }
        
         # If the node has a parent, retrieve its field name (if any)
        if node.parent:
            for i in range(node.parent.child_count):
                if node.parent.child(i) == node:
                    props["field_name"] = node.parent.field_name_for_child(i)
                    break
        
        if node_type in TSNodeGroup.NODES_WITH_TEXT:
            props["text"] = self.src_bytes[node.start_byte : node.end_byte].decode("utf8")
        elif node_type in TSNodeGroup.NODES_WITH_TEXT_MASKED:
            props["text"] = f"{{{node_type}}}"
            
        elif node_type == TSNodeGroup.MODULE:
            props["path"] = utils.get_relative_path(self.path, self.repo_path)
            
        if node_type in TSNodeGroup.ELEMENTARY_TYPES:
            props["inferred_type"] = TypePairs.covert_ts_to_py_type(node_type)
            
        return props
    
    def generate_dummy_node(self, node: Node, dummy_field_name: str):
        props = self.get_node_properties(node)
        props["type"] = "dummy"
        props["field_name"] = dummy_field_name
        props["text"] = None
        return props