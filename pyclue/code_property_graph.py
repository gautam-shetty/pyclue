import networkx as nx
import json
import logging
import os
import concurrent.futures

from abstract_syntax_tree import AbstractSyntaxTree
from control_flow_graph import ControlFlowGraph
from data_flow_graph import DataFlowGraph
from visitor import GraphVisitor
from constants import AppConfig
import utils

class CodePropertyGraph:
    def __init__(self, dir):
        self.dir = dir
        self.graph = nx.MultiDiGraph()
        self.visitor = GraphVisitor()
        self.logger = logging.getLogger(self.__class__.__name__)
        
    def _generate_ast_for_file(self, file_path):
        """
        Generate the AST for a single file, returning nodes and edges.
        """
        try:
            ast = AbstractSyntaxTree(repo_path=self.dir, file_path=file_path)
            nodes, edges = ast.generate_nodes_and_edges(ast.tree.root_node)
            self.logger.info(f"AST generated for file: \033[94m{file_path}\033[0m")
            return nodes, edges  # Return nodes and edges instead of modifying graph directly
        except Exception as e:
            self.logger.error(f"Error generating AST for file: {file_path}")
            self.logger.error(e)
            return [], []  # Return empty lists on error

    def generate_asts(self):
        """
        Generate ASTs for all files in the target directory using multiprocessing.
        """
        file_paths = list(utils.traverse_directory(self.dir, 
                                                   restrict_extensions=AppConfig.SUPPORTED_FILE_EXTENSIONS, 
                                                   ignore_dirs=AppConfig.IGNORE_DIRECTORIES))

        # Use ProcessPoolExecutor to fully utilize CPU cores
        with concurrent.futures.ProcessPoolExecutor() as executor:
            results = executor.map(self._generate_ast_for_file, file_paths)

        # Add nodes and edges to the graph after ASTs are generated
        for nodes, edges in results:
            self.graph.add_nodes_from(nodes)
            self.graph.add_edges_from(edges)
            
    def generate_cfgs(self):
        """
        Generate Control Flow edges.
        """
        try:
            cfg = ControlFlowGraph(self.graph)
            edges = cfg.generate_control_flow_edges()
            self.graph.add_edges_from(edges)
        except Exception as e:
            self.logger.error(f"Error generating CFG: {e}")
    
    def generate_dfgs(self):
        """
        Generate Data Flow edges.
        """
        try:
            dfg = DataFlowGraph(self.graph)
            dfg.generate_definitions()
            edges = dfg.generate_data_flow_edges()
            self.graph.add_edges_from(edges)
        except Exception as e:
            self.logger.error(f"Error generating DFG: {e}") 
           
    def export(self, output_path):
        # Create the base folder if it does not exist
        base_folder = os.path.dirname(output_path)
        if not os.path.exists(base_folder):
            os.makedirs(base_folder)
        
        file_extension = output_path.split('.')[-1].lower()
        
        if file_extension == 'json':
            # Convert the graph to a dictionary
            data = nx.readwrite.json_graph.node_link_data(self.graph)
            with open(output_path, 'w') as f:
                json.dump(data, f, indent=2)
        else:
            raise NotImplementedError(f"Unsupported file format: {file_extension}, current supported format is .json")