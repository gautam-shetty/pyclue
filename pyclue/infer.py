import logging
from code_property_graph import CodePropertyGraph
from visitor import GraphVisitor, GraphTreeVisitor, NXAlgorithms
from rules import TypeInferenceRules
from constants import EdgeType, DummyNode, TSNodeGroup, TypeInfrnNodeGroup
from utils import type_seperator

class TypeInference:
    def __init__(self, cpg: CodePropertyGraph):
        self.cpg = cpg
        self.logger = logging.getLogger(self.__class__.__name__)

    def infer_types(self):
        for n in GraphVisitor.get_nodes_by_type(self.cpg.graph, node_type=TSNodeGroup.DUMMY):
            n_data = GraphVisitor.get_node_by_id(self.cpg.graph, n)
            if n_data.get("field_name") == DummyNode.START:
                self.process_control_flow(n)
                
        # FIXME: temp fix to rerun type inference for function blocks to overwrite inferred types based on calls
        for n in GraphVisitor.get_nodes_by_type(self.cpg.graph, node_type=TSNodeGroup.DUMMY):
            n_data = GraphVisitor.get_node_by_id(self.cpg.graph, n)
            if n_data.get("field_name") == DummyNode.ENTRY:
                self.process_control_flow(n)
                
    def process_control_flow(self, node, preload_pairs=None):
        try:
            if preload_pairs:
                preload_pair_idx = 0
                unnamed_preload_pair_count = GraphTreeVisitor.unnamed_arg_pair_count(preload_pairs)
                named_preload_pairs = []
                name_preload_table = {}
                
                if unnamed_preload_pair_count > 0:
                    named_preload_pairs = preload_pairs[unnamed_preload_pair_count:]
                    for pair in named_preload_pairs:
                        key_text = GraphVisitor.get_node_by_id(self.cpg.graph, pair[0]).get('text')
                        value_text = GraphVisitor.get_node_by_id(self.cpg.graph, pair[1]).get('text')
                        name_preload_table[key_text] = value_text
                
            for curr, successors, _ in GraphVisitor.walk_nodes_by_edge_type(self.cpg.graph, source_node=node, edge_type=EdgeType.CF):
                curr_data = GraphVisitor.get_node_by_id(self.cpg.graph, curr)
                
                if curr_data.get("type") in TypeInfrnNodeGroup.STMTS_TYPES:
                    self.infer_type_for_statement(curr)
                elif curr_data.get("type") in TSNodeGroup.FN_PARAM_BLOCK:
                    if preload_pairs:
                        val = None
                        if curr_data.get("type") == TSNodeGroup.IDENTIFIER:
                            if preload_pair_idx < unnamed_preload_pair_count:
                                key, val = preload_pairs[preload_pair_idx]
                                preload_pair_idx += 1
                            else:
                                if curr_data.get("text") in name_preload_table:
                                    val = name_preload_table[curr_data.get("text")]
                        elif curr_data.get("type") == TSNodeGroup.FN_DEFAULT_PARAM:
                            # TODO: handle default parameter type pairing
                            pass
                            
                        if val:
                            val_type = self._infer_type(val)
                            GraphVisitor.update_node(self.cpg.graph, curr, {'inferred_type': val_type})
                            # check if lhs has outdegree of DF
                            for u, v, _ in GraphVisitor.get_outdegree_edges_by_type(self.cpg.graph, curr, EdgeType.DF):
                                self.propogate_type(source=u, target=v)
                    #TODO: default parameter type pairing
                             
                    if curr_data.get("type") in [TSNodeGroup.FN_TYPED_DEFAULT_PARAM, TSNodeGroup.FN_TYPED_PARAM]:
                        identifier_node = GraphVisitor.get_child_by_type(self.cpg.graph, curr, TSNodeGroup.IDENTIFIER)
                        annotated_type_node = GraphVisitor.get_child_by_field_name(self.cpg.graph, curr, 'type')
                        calculated_type = self._infer_annotation_type(identifier_node, annotated_type_node)
                        
                        GraphVisitor.update_node(self.cpg.graph, curr, {'inferred_type': calculated_type})
                        # check if lhs has outdegree of DF
                        for u, v, _ in GraphVisitor.get_outdegree_edges_by_type(self.cpg.graph, curr, EdgeType.DF):
                            self.propogate_type(source=u, target=v)
                            
                elif curr_data.get("type") in TSNodeGroup.DUMMY and curr_data.get("field_name") == DummyNode.RETURN:
                    fn_node = GraphVisitor.get_parent(self.cpg.graph, curr, EdgeType.AST)
                    if fn_node:
                        annotated_return_node = GraphVisitor.get_child_by_field_name(self.cpg.graph, fn_node, 'return_type')
                        if annotated_return_node:
                            self._infer_annotation_type(curr, annotated_return_node)
                        
                        # GraphVisitor.update_node(self.cpg.graph, curr, {'inferred_type': calculated_return_type})
                        # # check if lhs has outdegree of DF
                        # for u, v, _ in GraphVisitor.get_outdegree_edges_by_type(self.cpg.graph, curr, EdgeType.DF):
                        #     self.propogate_type(source=u, target=v)
                    
            self.log_control_flow(node)
        except Exception as e:
            self.logger.error(f"Inference failed for block {node}.")
            self.logger.warning(f"Warning Message: {e}", exc_info=True)

    def log_control_flow(self, dummy_node):
        block_type = None
        block_name = None
        for pred in GraphVisitor.immediate_predecessors(self.cpg.graph, dummy_node):
            block_type = GraphVisitor.get_node_by_id(self.cpg.graph, pred)["type"]
            
            if block_type == TSNodeGroup.MODULE:
                block_name = GraphVisitor.get_node_by_id(self.cpg.graph, pred).get("path")
            else:
                block_name = GraphVisitor.get_node_by_id(self.cpg.graph, GraphVisitor.get_child_by_field_name(self.cpg.graph, pred, "name")).get("text")
                
            break
        
        self.logger.info(f"Control flow processed for \033[92m{block_type}\033[0m: \033[94m{block_name}\033[0m.")

    def infer_type_for_statement(self, node):
        return_mode = False
        
        node_data = GraphVisitor.get_node_by_id(self.cpg.graph, node)
        if node_data.get("type") in TSNodeGroup.RETURN_STMT:
            return_mode = True
        
        for succ in GraphVisitor.immediate_successors(self.cpg.graph, node):
            n_type = GraphVisitor.get_node_by_id(self.cpg.graph, succ).get('type')
            
            if n_type == TSNodeGroup.ASGMT:
                anntd_asgmt = GraphVisitor.get_child_by_field_name(self.cpg.graph, succ, 'type')
                
                if anntd_asgmt:
                    annotated_type_node = GraphVisitor.get_child_by_field_name(self.cpg.graph, succ, 'type')
                    lhs, rhs = GraphTreeVisitor.assignment_pairs(self.cpg.graph, succ)[0]
                    calculated_type = self._infer_annotation_type(lhs, annotated_type_node)
                    
                    GraphVisitor.update_node(self.cpg.graph, succ, {'inferred_type': calculated_type})
                            
                    # check if lhs has outdegree of DF
                    for u, v, _ in GraphVisitor.get_outdegree_edges_by_type(self.cpg.graph, succ, EdgeType.DF):
                        self.propogate_type(source=u, target=v)
                else:
                    for lhs, rhs in GraphTreeVisitor.assignment_pairs(self.cpg.graph, succ):
                        rhs_calcd_type = self._infer_type(rhs)
                        
                        if rhs_calcd_type:
                            # update left type
                            GraphVisitor.update_node(self.cpg.graph, lhs, {'inferred_type': rhs_calcd_type})
                            
                        # check if lhs has outdegree of DF
                        for u, v, _ in GraphVisitor.get_outdegree_edges_by_type(self.cpg.graph, lhs, EdgeType.DF):
                            self.propogate_type(source=u, target=v)
            elif n_type in TSNodeGroup.OPERATOR_TYPES + TSNodeGroup.GENERIC_TYPES + [TSNodeGroup.CALL]:
                calcd_type = self._infer_type(succ)
                
                if calcd_type:
                    GraphVisitor.update_node(self.cpg.graph, node, {'inferred_type': calcd_type})
                        
                # check if lhs has outdegree of DF
                for u, v, _ in GraphVisitor.get_outdegree_edges_by_type(self.cpg.graph, succ, EdgeType.DF):
                    self.propogate_type(source=u, target=v)
    
        if return_mode:
            for u, v, _ in GraphVisitor.get_outdegree_edges_by_type(self.cpg.graph, node, EdgeType.DF):
                self.propogate_type(source=u, target=v)
    
    def _infer_type(self, node):
        #FIXME: stack the types while resolving this block rather than storing to graph directly
        stmt_graph = GraphVisitor.generate_subgraph(self.cpg.graph, node, EdgeType.AST)
        resolve_order = NXAlgorithms.topological_sort(stmt_graph)
        
        for each in resolve_order:
            each_type = GraphVisitor.get_node_by_id(stmt_graph, each).get('type')

            calculated_type = None
            if each_type in TSNodeGroup.OPERATOR_TYPES:
                calculated_type = self._infer_type_for_operator(each)
            elif each_type in TSNodeGroup.GENERIC_TYPES:
                calculated_type = self._infer_type_for_generic(each)
            elif each_type in TSNodeGroup.CALL:
                calculated_type = self._infer_type_for_call(each)
                
            if calculated_type:
                GraphVisitor.update_node(self.cpg.graph, each, {'inferred_type': calculated_type})
                    
        return GraphVisitor.get_node_by_id(self.cpg.graph, node).get('inferred_type')
    
    def _infer_annotation_type(self, annotation_target_node, annotation_node):
        annotated_type_text = GraphVisitor.get_node_by_id(self.cpg.graph, annotation_node).get('text')
        
        GraphVisitor.update_node(self.cpg.graph, annotation_target_node, {'inferred_type': annotated_type_text})
        # check if lhs has outdegree of DF
        for u, v, _ in GraphVisitor.get_outdegree_edges_by_type(self.cpg.graph, annotation_target_node, EdgeType.DF):
            self.propogate_type(source=u, target=v)
            
        return annotated_type_text
    
    def _infer_type_for_call(self, node):
        resolved_type = None
        fn_return = None
        call_name_node = GraphVisitor.get_child_by_field_name(self.cpg.graph, node, 'function')
        params_pairs = GraphTreeVisitor.argument_pairs(self.cpg.graph, node)
        
        if call_name_node:
            call_def_name = GraphVisitor.get_parent(self.cpg.graph, call_name_node, EdgeType.DF)
            
            if call_def_name:
                call_def = GraphVisitor.get_parent(self.cpg.graph, call_def_name, EdgeType.AST)
            
                if call_def:
                    call_def_type = GraphVisitor.get_node_by_id(self.cpg.graph, call_def).get('type')
                    
                    if call_def_type == TSNodeGroup.FN_NODE:
                        fn_entry = GraphVisitor.get_child_by_field_name(self.cpg.graph, call_def, DummyNode.ENTRY)
                        fn_return = GraphVisitor.get_child_by_field_name(self.cpg.graph, call_def, DummyNode.RETURN)
                        self.process_control_flow(fn_entry, preload_pairs=params_pairs)
                    elif call_def_type == TSNodeGroup.CLS_NODE:
                        # Class / user defined type
                        resolved_type = GraphVisitor.get_node_by_id(self.cpg.graph, call_def_name).get('text')
                    
        if fn_return:
            resolved_type = GraphVisitor.get_node_by_id(self.cpg.graph, fn_return).get('inferred_type')
        
        return resolved_type

    def _infer_type_for_operator(self, node):
        left_n = GraphVisitor.get_child_by_field_name(self.cpg.graph, node, 'left')
        operator_n = GraphVisitor.get_child_by_field_name(self.cpg.graph, node, 'operator')
        right_n = GraphVisitor.get_child_by_field_name(self.cpg.graph, node, 'right')
        
        left_type = GraphVisitor.get_node_by_id(self.cpg.graph, left_n).get('inferred_type') if left_n else None
        operator = GraphVisitor.get_node_by_id(self.cpg.graph, operator_n).get('type') if operator_n else None
        right_type = GraphVisitor.get_node_by_id(self.cpg.graph, right_n).get('inferred_type') if right_n else None
        
        if left_type and operator and right_type:
            resolved_type = TypeInferenceRules.get_expr_type(
                left_type = left_type, 
                operator = operator, 
                right_type = right_type
            )
            return resolved_type
        return None
    
    def _infer_type_for_generic(self, node):
        genetric_type = GraphVisitor.get_node_by_id(self.cpg.graph, node).get('type')
        
        value_types = []
        key_types = []
        for child in GraphVisitor.immediate_successors(self.cpg.graph, node, sort=True):
            child_data = GraphVisitor.get_node_by_id(self.cpg.graph, child)
            
            if child_data.get('type') in TSNodeGroup.ELEMENTARY_TYPES + TSNodeGroup.GENERIC_TYPES + [TSNodeGroup.IDENTIFIER]:
                value_types.append(child_data.get('inferred_type'))
            elif child_data.get('type') == TSNodeGroup.DICT_PAIR:
                _, key_n_data = GraphVisitor.get_child_by_field_name(self.cpg.graph, child, 'key', data=True)
                if key_n_data.get('type') in TSNodeGroup.ELEMENTARY_TYPES + TSNodeGroup.GENERIC_TYPES + [TSNodeGroup.IDENTIFIER]:
                    key_types.append(key_n_data.get('inferred_type'))
                
                _, value_n_data = GraphVisitor.get_child_by_field_name(self.cpg.graph, child, 'value', data=True)
                if value_n_data.get('type') in TSNodeGroup.ELEMENTARY_TYPES + TSNodeGroup.GENERIC_TYPES + [TSNodeGroup.IDENTIFIER]:
                    value_types.append(value_n_data.get('inferred_type'))

        resolved_type = TypeInferenceRules.get_generic_type(genetric_type, value_types, key_types)
        return resolved_type

    def propogate_type(self, source, target):
        source_data = GraphVisitor.get_node_by_id(self.cpg.graph, source)
        inferred_type = source_data.get('inferred_type')
        
        # Check if target has more than one in-degree edge with key 'CF'
        in_edges = GraphVisitor.get_indegree_edges_by_type(self.cpg.graph, target, EdgeType.DF)
        if len(in_edges) > 1:
            existing_type = GraphVisitor.get_node_by_id(self.cpg.graph, target).get('inferred_type')
            if existing_type:
                inferred_type = TypeInferenceRules.merge_types(type_seperator(existing_type) + [inferred_type])
        
        GraphVisitor.update_node(self.cpg.graph, target, {'inferred_type': inferred_type})