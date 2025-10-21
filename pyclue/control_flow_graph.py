import networkx as nx
import logging

from visitor import GraphVisitor
import sequence_manager as sm
from constants import TSNodeGroup, DummyNode, EdgeType

"""
Abbrevaitions:
n - node
s - Sequence
h - head
t - tail
"""

class ControlFlowGraph:
    def __init__(self, graph: nx.MultiDiGraph):
        self.graph = graph
        self.logger = logging.getLogger(self.__class__.__name__)
        self.cf_edges = []
        
    def generate_control_flow_edges(self):
        def log(block_type, block_name):
            self.logger.info(f"CF generated for \033[92m{block_type}\033[0m: \033[94m{block_name}\033[0m")
        
        for n, n_type in self.graph.nodes(data="type"):
            try:
                if n_type in TSNodeGroup.MODULE:
                    module_s = self.get_module_seq(n)
                    module_s.generate_edges(EdgeType.CF)
                    self.cf_edges.extend(module_s.edges)
                    log(n_type, GraphVisitor().get_node_by_id(self.graph, n)["path"])
                elif n_type == TSNodeGroup.CLS_NODE:
                    cls_s = self.get_cls_seq(n)
                    cls_s.generate_edges(EdgeType.CF)
                    self.cf_edges.extend(cls_s.edges)
                    log(n_type, GraphVisitor().get_node_by_id(self.graph, GraphVisitor().get_child_by_field_name(self.graph, n, "name"))["text"])
                elif n_type == TSNodeGroup.FN_NODE:
                    fn_s = self.get_fn_seq(n)
                    fn_s.generate_edges(EdgeType.CF)
                    self.cf_edges.extend(fn_s.edges)
                    log(n_type, GraphVisitor().get_node_by_id(self.graph, GraphVisitor().get_child_by_field_name(self.graph, n, "name"))["text"])
            except Exception as e:
                self.logger.warning(f"Failed to generate CF edges for block {n} of type {n_type}.")
                self.logger.warning(f"Warning Message: {e}")
        
        return self.cf_edges
    
    def get_block_seq(self, block, filter_by_type=None):    
        s = sm.Sequence()
        
        for n in GraphVisitor().immediate_successors(self.graph, block, filter_by_type, sort=True):
            n_type = GraphVisitor().get_node_by_id(self.graph, n)["type"]
        
            if n_type == TSNodeGroup.DUMMY:
                continue
            elif n_type == TSNodeGroup.CONDITIONAL_IF:
                s.add_item(self.get_main_conditional_seq(n))
            elif n_type in TSNodeGroup.LOOP:
                s.add_item(self.get_loop_seq(n))
            elif n_type == TSNodeGroup.EXCEPTION_TRY:
                s.add_item(self.get_try_seq(n))
            else:
                # simple node
                s.add_item(sm.Node(n))

        return s
    
    def get_module_seq(self, module):
        s = self.get_block_seq(module)
        s.add_at_start(sm.Node(GraphVisitor().get_child_by_field_name(self.graph, module, DummyNode.START)))
        s.add_at_end(sm.Node(GraphVisitor().get_child_by_field_name(self.graph, module, DummyNode.EXIT)))
        
        return s
    
    def get_cls_seq(self, cls):
        s = sm.Sequence()
        
        for n in GraphVisitor().immediate_successors(self.graph, cls, sort=True):
            n_type = GraphVisitor().get_node_by_id(self.graph, n)["type"]
            
            if n_type == TSNodeGroup.BLOCK:
                s.extend_sequence(self.get_block_seq(n).items)
                
        s.add_at_start(sm.Node(GraphVisitor().get_child_by_field_name(self.graph, cls, DummyNode.START)))
        s.add_at_end(sm.Node(GraphVisitor().get_child_by_field_name(self.graph, cls, DummyNode.EXIT)))
        
        return s
    
    def get_fn_seq(self, fn):
        s = sm.Sequence()
        
        for n in GraphVisitor().immediate_successors(self.graph, fn, sort=True):
            n_type = GraphVisitor().get_node_by_id(self.graph, n)["type"]
            
            if n_type == TSNodeGroup.FN_PARAMS:
                # Custom block for function parameters
                s.extend_sequence(self.get_block_seq(n, filter_by_type=TSNodeGroup.FN_PARAM_BLOCK).items)
            elif n_type == TSNodeGroup.BLOCK:
                s.extend_sequence(self.get_block_seq(n).items)
                
        s.add_at_start(sm.Node(GraphVisitor().get_child_by_field_name(self.graph, fn, DummyNode.ENTRY)))
        s.add_at_end(sm.Node(GraphVisitor().get_child_by_field_name(self.graph, fn, DummyNode.RETURN)))
                
        return s
    
    def get_main_conditional_seq(self, conditional):
        cond_s = sm.ConditionalSequence()
        
        main_condition_n, main_block_s = self._get_conditional_seq(conditional)
        cond_s.add_sequence(main_condition_n, main_block_s)
    
        for n in GraphVisitor().immediate_successors(self.graph, conditional, sort=True):
            n_type = GraphVisitor().get_node_by_id(self.graph, n)["type"]
                
            if n_type in TSNodeGroup.CONDITIONAL_ALTERNATIVE:
                alt_condition_n, alt_block_s = self._get_conditional_seq(n)
                if alt_condition_n is None:
                    alt_condition_n = "else"
                cond_s.add_sequence(alt_condition_n, alt_block_s)
        
        return cond_s
    
    def _get_conditional_seq(self, conditional):
        condition_n = None
        block_s = sm.Sequence()
        
        for n in GraphVisitor().immediate_successors(self.graph, conditional, sort=True):
            n_data: dict = GraphVisitor().get_node_by_id(self.graph, n)
            
            if "condition" == n_data.get("field_name"):
                condition_n = n
                
            if TSNodeGroup.BLOCK == n_data.get("type"):
                block_s = self.get_block_seq(n)
            
        return condition_n, block_s
    
    def get_loop_seq(self, loop):
        loop_s = sm.LoopSequence()
        _type = GraphVisitor().get_node_by_id(self.graph, loop)["type"]
        
        if _type == TSNodeGroup.FOR_LOOP:
            right = GraphVisitor().get_child_by_field_name(self.graph, loop, "right")
            loop_s.main_s.add_item(sm.Node(right))
            
            left = GraphVisitor().get_child_by_field_name(self.graph, loop, "left")
            loop_s.left_id = left
            loop_s.main_s.add_item(sm.Node(left))
        elif _type == TSNodeGroup.WHILE_LOOP:
            left = GraphVisitor().get_child_by_field_name(self.graph, loop, "condition")
            loop_s.left_id = left
            loop_s.main_s.add_item(sm.Node(left))
        
        block = GraphVisitor().get_child_by_field_name(self.graph, loop, "body")
        loop_s.block_s.extend_sequence(self.get_block_seq(block).items)
                
        return loop_s
    
    def get_try_seq(self, exception):
        excp_s = sm.ExceptionSequence()
        
        _, try_block = self._get_exception_seq(exception)
        excp_s.try_s.extend_sequence(try_block.items)
        
        for n in GraphVisitor().immediate_successors(self.graph, exception, sort=True):
            n_type = GraphVisitor().get_node_by_id(self.graph, n)["type"]
            
            if n_type == TSNodeGroup.EXCEPTION_EXCEPT:
                excp_n, except_block = self._get_exception_seq(n)
                if excp_n:
                    excp_s.add_except_sequence(excp_n, except_block)
                else:
                    excp_s.add_except_sequence("except", except_block)
            elif n_type == TSNodeGroup.EXCEPTION_FINALLY:
                _, finally_block = self._get_exception_seq(n)
                excp_s.finally_s.extend_sequence(finally_block.items)
        
        return excp_s
    
    def _get_exception_seq(self, exception):
        exception_n = None
        block_s = sm.Sequence()
        
        for n in GraphVisitor().immediate_successors(self.graph, exception, sort=True):
            n_type = GraphVisitor().get_node_by_id(self.graph, n)["type"]
            
            # NOTE: Can a single except clause have multiple exceptions to catch?
            if n_type in [TSNodeGroup.IDENTIFIER, TSNodeGroup.AS_PATTERN]:
                exception_n = n
            elif n_type == TSNodeGroup.BLOCK:
                block_s = self.get_block_seq(n)
    
        return exception_n, block_s
        