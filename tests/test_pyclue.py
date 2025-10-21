import pytest
import os
import json
import networkx as nx
from pyclue.code_property_graph import CodePropertyGraph

def test_cpg():
    # test_dir = 'repos/toy_project_1'
    test_dir = os.path.join(os.path.dirname(__file__), 'repos/toy_project_1')
    
    truth_cpg = Utils.load_graph_from_json(os.path.join(test_dir, 'cpg.json'))
    test_cpg = CodePropertyGraph(dir=test_dir).graph
    
    assert_nodes_equal(test_cpg, truth_cpg)
    assert_edges_equal(test_cpg, truth_cpg, edge_type='AST')
    assert_edges_equal(test_cpg, truth_cpg, edge_type='CF')
    assert_edges_equal(test_cpg, truth_cpg, edge_type='DF')
    
def assert_nodes_equal(test_G: nx.MultiDiGraph, truth_G: nx.MultiDiGraph):
    for test_n, test_n_data in test_G.nodes(data=True):
        truth_n_data = truth_G.nodes.get(test_n, None)
        if truth_n_data is None:
            pytest.fail(f"Node {test_n} not found in the truth graph.")
        
        # Convert sets or tuples to lists in test_n_data
        # beacuse the truth graph has lists as json file does not support sets or tupless
        test_n_data = Utils.convert_node_data_to_list(test_n_data)
        
        assert test_n_data == truth_n_data, f"Node {test_n} data does not match with the truth graph."

def assert_edges_equal(test_G: nx.MultiDiGraph, truth_G: nx.MultiDiGraph, edge_type: str):
    test_edges = [(u, v, k) for u, v, k in test_G.edges(keys=True) if k == edge_type]
    truth_edges = [(u, v, k) for u, v, k in truth_G.edges(keys=True) if k == edge_type]
    assert set(test_edges) == set(truth_edges), f"Edges of type {edge_type} do not match"

class Utils:
    @staticmethod
    def load_graph_from_json(json_file_path):
        data = json.load(open(json_file_path, 'r'))
        G = nx.node_link_graph(data)
        
        return G
    
    @staticmethod
    def convert_node_data_to_list(node_data: dict):
        return {k: list(v) if isinstance(v, (set, tuple)) else v for k, v in node_data.items()}