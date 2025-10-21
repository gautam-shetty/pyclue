import logging
import networkx as nx

from visitor import GraphVisitor, GraphTreeVisitor
from constants import TSNodeGroup, DummyNode, EdgeType
from utils import module_path_to_dotted_name

class Definitions:
    def __init__(self):
        self.table = {}

    def add(self, text: str, node_id: str):
        if text not in self.table:
            self.table[text] = {"id": node_id}
        else:
            self.table[text]["id"] = node_id

    def add_children(self, text: str, children):
        if text not in self.table:
            self.table[text] = {"children": children}
        else:
            self.table[text]["children"] = children

    def get(self, text: str):
        return self.table.get(text)
    
class FlowLiveness:
    def __init__(self):
        self.table = {}
        self.merge_mode = False
        
    def add(self, text: str, node_id: str):
        if self.merge_mode and text in self.table:
            if isinstance(self.table[text], list):
                self.table[text].append(node_id)
            else:
                self.table[text] = [self.table[text], node_id]
        else:
            self.table[text] = node_id
        
    def get(self, text: str):
        return self.table.get(text)

class DataFlowGraph:
    def __init__(self, graph: nx.MultiDiGraph):
        self.graph = graph
        self.logger = logging.getLogger(self.__class__.__name__)
        self.definitions = Definitions()
        self.df_edges = []
        
    def generate_definitions(self):
        
        def generate_children_definitions(node):
            children_definition = Definitions()
                        
            dummy, dummy_data = GraphVisitor().get_child_by_type(self.graph, node, TSNodeGroup.DUMMY, data=True)
            if dummy_data["field_name"] not in [DummyNode.START, DummyNode.ENTRY]:
                return children_definition
            
            for curr, _, _ in GraphVisitor().walk_nodes_by_edge_type(self.graph, source_node=dummy, edge_type=EdgeType.CF):
                curr_data = GraphVisitor().get_node_by_id(self.graph, curr)
                curr_type = curr_data.get("type")
        
                if curr_type in [TSNodeGroup.CLS_NODE, TSNodeGroup.FN_NODE]:
                    n_name, n_name_data = GraphVisitor().get_child_by_field_name(self.graph, curr, "name",data=True)
                    text = n_name_data.get("text")
                    children_definition.add(text, curr)
                    children_definition.add_children(text, generate_children_definitions(curr))
                elif curr_type == TSNodeGroup.EXPR_STMT:
                    for succ in GraphVisitor().immediate_successors(self.graph, curr):
                        n_type = GraphVisitor().get_node_by_id(self.graph, succ)["type"]
                        
                        if n_type == TSNodeGroup.ASGMT:
                            for lhs, _ in GraphTreeVisitor.assignment_pairs(self.graph, succ):
                                lhs_data = GraphVisitor().get_node_by_id(self.graph, lhs)
                                lhs_type = lhs_data.get("type")
                                
                                if lhs_type == TSNodeGroup.IDENTIFIER:
                                    lhs_text = lhs_data.get("text")
                                    if lhs_text:
                                        children_definition.add(lhs_text, lhs)
                                        children_definition.add_children(lhs_text, Definitions())
                    
            return children_definition
        
        for n in GraphVisitor().get_nodes_by_type(self.graph, node_type=TSNodeGroup.MODULE):
            try:
                n_data = GraphVisitor().get_node_by_id(self.graph, n)
                
                module_text = module_path_to_dotted_name(module_path = n_data.get("path"))
                self.definitions.add(module_text, node_id=n)
                self.definitions.add_children(module_text, generate_children_definitions(n))
                    
            except Exception as e:
                self.logger.warning(f"Failed to get definitions for block {n} | {n_data}")
                self.logger.warning(f"Warning Message: {e}")
        
    def generate_data_flow_edges(self):
        def log(dummy_node, edge_count):
            block_type = None
            block_name = None
            for pred in GraphVisitor().immediate_predecessors(self.graph, dummy_node):
                block_type = GraphVisitor().get_node_by_id(self.graph, pred)["type"]
                
                if block_type == TSNodeGroup.MODULE:
                    block_name = GraphVisitor().get_node_by_id(self.graph, pred).get("path")
                else:
                    block_name = GraphVisitor().get_node_by_id(self.graph, GraphVisitor().get_child_by_field_name(self.graph, pred, "name")).get("text")
                    
                break
            
            self.logger.info(f"DF generated for \033[92m{block_type}\033[0m: \033[94m{block_name}\033[0m. Edges added: {edge_count - curr_df_edge_count}")

        curr_df_edge_count = len(self.df_edges)
        for n in GraphVisitor().get_nodes_by_type(self.graph, node_type=TSNodeGroup.DUMMY):
            try:
                n_data = GraphVisitor().get_node_by_id(self.graph, n)
                if n_data["field_name"] in [DummyNode.START, DummyNode.ENTRY]:
                    self.process_control_flow(n)
                    log(n, len(self.df_edges))
                    curr_df_edge_count = len(self.df_edges)
            except Exception as e:
                self.logger.warning(f"Failed to generate DF edges for block {n}.")
                self.logger.warning(f"Warning Message: {e}", exc_info=True)

        return self.df_edges
    
    def process_control_flow(self, node):
        liveness = FlowLiveness()
        self.preload_constants(module_path=GraphVisitor().get_node_by_id(self.graph, node).get("module"), liveness=liveness)
        
        for curr, successors, delayed_nodes in GraphVisitor().walk_nodes_by_edge_type(self.graph, source_node=node, edge_type=EdgeType.CF):
            curr_data = GraphVisitor().get_node_by_id(self.graph, curr)

            
            if delayed_nodes:
                liveness.merge_mode = True
            else:
                liveness.merge_mode = False
            
            # import resolution
            if curr_data["type"] in TSNodeGroup.IMPORTS:
                for import_pair in GraphTreeVisitor.get_import_pairs(self.graph, curr):
                    module, symbol, alias = import_pair
                    
                    if module:
                        module_data = GraphVisitor().get_node_by_id(self.graph, module)
                    else:
                        module_data = None
                        
                    if symbol:
                        symbol_data = GraphVisitor().get_node_by_id(self.graph, symbol)
                    else:
                        symbol_data = None
                    
                    if alias:
                        self.add_to_liveness(liveness, alias)
                    else:
                        if symbol:
                            symbol_text = symbol_data.get("text")
                            module_text = module_data.get("text")
                            
                            if module_text and symbol_text == "*":
                                module_def = self.definitions.get(module_text)
                                if module_def:
                                    for child_text, child_def in module_def.get("children", {}).table.items():
                                        liveness.add(child_text, child_def["id"])
                            else:
                                self.add_to_liveness(liveness, symbol)
                        else:
                            if module:
                                self.add_to_liveness(liveness, module)

                    
                    if module_data:
                        module_text = module_data.get("text")
                        if module_text:
                            module_def = self.definitions.get(module_text)                            
                            if module_def:
                                module_def_id = module_def.get("id")
                                self.df_edges.append((module_def_id, module, EdgeType.DF))
                                
                    
                    if symbol_data:
                        module_text = module_data.get("text")
                        symbol_text = symbol_data.get("text")
                        if symbol_text:
                            module_def = self.definitions.get(module_text)
                            if module_def:
                                module_def_children = module_def.get("children")                                
                                if module_def_children:
                                    symbol_def = module_def_children.get(symbol_text)
                                    if symbol_def:
                                        symbol_def_id = symbol_def.get("id")
                                        self.df_edges.append((symbol_def_id, symbol, EdgeType.DF))
            
            # expression statement (assignment, call, etc.)
            elif curr_data["type"] == TSNodeGroup.EXPR_STMT:
                use_nodes, def_nodes = self.get_use_and_def_nodes(curr)
                for def_node in def_nodes:
                    self.add_to_liveness(liveness, def_node)
                        
                for use_node in use_nodes:
                    use_node_def = self.get_from_liveness(liveness, use_node)
                    if use_node_def:
                        if isinstance(use_node_def, list):
                            for def_node in use_node_def:
                                self.df_edges.append((def_node, use_node, EdgeType.DF))
                        else:
                            self.df_edges.append((use_node_def, use_node, EdgeType.DF))
                        
            # return statement
            elif curr_data["type"] == TSNodeGroup.RETURN_STMT:
                use_nodes, _ = self.get_use_and_def_nodes(curr)
                for use_node in use_nodes:
                    use_node_def = self.get_from_liveness(liveness, use_node)
                    if use_node_def:
                        if isinstance(use_node_def, list):
                            for def_node in use_node_def:
                                self.df_edges.append((def_node, use_node, EdgeType.DF))
                        else:
                            self.df_edges.append((use_node_def, use_node, EdgeType.DF))
                
                # to link all return statements to the dummy node         
                for succ in GraphVisitor().immediate_successors(self.graph, curr):
                    n_type = GraphVisitor().get_node_by_id(self.graph, succ)["type"]
                    
                    if n_type == TSNodeGroup.DUMMY:
                        if GraphVisitor().get_node_by_id(self.graph, succ)["field_name"] == DummyNode.RETURN:
                            self.df_edges.append((curr, succ, EdgeType.DF))
                        
            elif curr_data["type"] in TSNodeGroup.DEF_NODES:
                n_name = GraphVisitor().get_child_by_field_name(self.graph, curr, "name")
                self.add_to_liveness(liveness, n_name)
                
            elif curr_data["type"] == TSNodeGroup.IDENTIFIER:
                self.add_to_liveness(liveness, curr)
    
        return liveness
    
    def preload_constants(self, module_path: str, liveness: FlowLiveness):
        module_text = module_path_to_dotted_name(module_path)
        module_def = self.definitions.get(module_text)
        if module_def:
            for child_text, child_def in module_def.get("children", {}).table.items():
                child_text: str
                if child_text.isupper():
                    liveness.add(child_text, child_def["id"])
    
    def get_use_and_def_nodes(self, node):
        use_nodes, def_nodes = [], []
        
        for succ in GraphVisitor().immediate_successors(self.graph, node):
            n_type = GraphVisitor().get_node_by_id(self.graph, succ)["type"]
            
            if n_type == TSNodeGroup.ASGMT:
                for lhs, rhs in GraphTreeVisitor.assignment_pairs(self.graph, succ):
                    rhs_data = GraphVisitor().get_node_by_id(self.graph, rhs)
                    lhs_data = GraphVisitor().get_node_by_id(self.graph, lhs)
                    
                    use_nodes.extend(GraphVisitor().find_nodes_by_type_from_source(self.graph, source_node=rhs, target_type=TSNodeGroup.IDENTIFIER))
                        
                    if lhs_data.get("type") == TSNodeGroup.IDENTIFIER:
                        def_nodes.append(lhs)
            elif n_type in [TSNodeGroup.CALL] + TSNodeGroup.GENERIC_TYPES + TSNodeGroup.OPERATOR_TYPES:
                use_nodes.extend(GraphVisitor().find_nodes_by_type_from_source(self.graph, source_node=succ, target_type=TSNodeGroup.IDENTIFIER))
            elif n_type == TSNodeGroup.ATTRIBUTE:
                obj, attribute_sequence = GraphTreeVisitor.get_object_attribute_sequence(self.graph, succ)
                if obj:
                    use_nodes.extend([obj])
            elif n_type == TSNodeGroup.EXPR_LIST: # used in return statement
                use_nodes.extend(GraphTreeVisitor.get_identifier_list(self.graph, succ))
            elif n_type == TSNodeGroup.IDENTIFIER: # used in return statement
                use_nodes.extend([succ])
                        
        return use_nodes, def_nodes
    
    def add_to_liveness(self, liveness: FlowLiveness, node):
        node_text = GraphVisitor().get_node_by_id(self.graph, node).get("text")
        if node_text and node_text != "":
            liveness.add(node_text, node)
            
    def get_from_liveness(self, liveness: FlowLiveness, node):
        node_text = GraphVisitor().get_node_by_id(self.graph, node).get("text")
        if node_text and node_text != "":
            return liveness.get(node_text)
        
        return None