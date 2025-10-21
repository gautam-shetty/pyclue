import networkx as nx
from collections import deque, defaultdict

from constants import TSNodeGroup, EdgeType

class GraphVisitor:
    @staticmethod
    def get_node_by_id(G: nx.MultiDiGraph, node_id: int) -> dict:
        """ Get a node from a MultiDiGraph by its ID.

        Args:
            G (nx.MultiDiGraph): The MultiDiGraph to search in.
            node_id (int): The ID of the node to retrieve.

        Returns:
            G.Node: The node with the specified ID.
        """
        return G.nodes[node_id]
    
    @staticmethod
    def update_node(G: nx.MultiDiGraph, node_id: int, attributes: dict):
        """
        Update attributes of a node in a MultiDiGraph.

        Args:
            G (nx.MultiDiGraph): The MultiDiGraph containing the node.
            node_id (int): The ID of the node to update.
            attributes (dict): A dictionary of attributes to update.

        Returns:
            None
        """
        for key, value in attributes.items():
            G.nodes[node_id][key] = value
    
    @staticmethod
    def get_child_by_type(G: nx.MultiDiGraph, node: str, type: str, data: bool = False):
        """
        Get a child node of a parent node by its type name.

        Args:
            G (nx.MultiDiGraph): The MultiDiGraph to search in.
            node (str): The ID of the parent node.
            type (str): The type name of the child node.
            data (bool): If True, return the node along with its data.

        Returns:
            Union[G.Node, Tuple[G.Node, dict]]: The child node with the specified type name,
            optionally with its data if data is True.
        """
        children = GraphVisitor.immediate_successors(G, node)
        for n in children:
            if G.nodes[n]['type'] == type:
                return (n, G.nodes[n]) if data else n
    
    
    @staticmethod
    def get_children_by_types(G: nx.MultiDiGraph, node: str, types: list, data: bool = False) -> list:
        """
        Get all child nodes of a parent node by their type names.

        Args:
            G (nx.MultiDiGraph): The MultiDiGraph to search in.
            node (str): The ID of the parent node.
            types (list): A list of type names of the child nodes.
            data (bool): If True, return the child nodes along with their data.

        Returns:
            List[Union[G.Node, Tuple[G.Node, dict]]]: A list of child nodes with the specified type names,
            optionally with their data if data is True.
        """
        children = GraphVisitor.immediate_successors(G, node)
        matched_children = [n for n in children if G.nodes[n].get('type') in types]
        if data:
            return [(n, G.nodes[n]) for n in matched_children]
        return matched_children
    
    @staticmethod
    def get_child_by_field_name(G: nx.MultiDiGraph, node: str, field_name: str, data: bool = False):
        """
        Get a child node of a parent node by its field name.

        Args:
            G (nx.MultiDiGraph): The MultiDiGraph to search in.
            node (str): The ID of the parent node.
            field_name (str): The field name of the child node.
            with_data (bool): If True, return the node along with its data.

        Returns:
            Union[G.Node, Tuple[G.Node, dict]]: The child node with the specified field name, 
            optionally with its data if with_data is True.
        """
        children = GraphVisitor.immediate_successors(G, node)
        for n in children:
            if G.nodes[n].get('field_name') == field_name:
                return (n, G.nodes[n]) if data else n

    @staticmethod
    def get_children_by_field_name(G: nx.MultiDiGraph, node: str, field_name: str, data: bool = False) -> list:
        """
        Get all child nodes of a parent node by their field name.

        Args:
            G (nx.MultiDiGraph): The MultiDiGraph to search in.
            node (str): The ID of the parent node.
            field_name (str): The field name of the child nodes.
            data (bool): If True, return the child nodes along with their data.

        Returns:
            List[Union[G.Node, Tuple[G.Node, dict]]]: A list of child nodes with the specified field name,
            optionally with their data if data is True.
        """
        children = GraphVisitor.immediate_successors(G, node)
        matched_children = [n for n in children if G.nodes[n].get('field_name') == field_name]
        if data:
            return [(n, G.nodes[n]) for n in matched_children]
        return matched_children
    
    @staticmethod
    def get_parent(G: nx.MultiDiGraph, node: str, edge_type=EdgeType.AST):
        """
        Get the parent (immediate predecessor) of a node by edge type.

        Args:
            G (nx.MultiDiGraph): The MultiDiGraph to search in.
            node (str): The ID of the node.
            edge_type (str): The type of the edge to filter by.

        Returns:
            Union[str, None]: The parent node ID if found, otherwise None.
        """
        for predecessor in G.predecessors(node):
            if G.has_edge(predecessor, node, key=edge_type):
                return predecessor
        return None
    
    @staticmethod
    def get_nodes_by_type(G: nx.MultiDiGraph, node_type: str):
        """
        Get nodes of a specific type from a MultiDiGraph.

        Parameters:
            G (nx.MultiDiGraph): The MultiDiGraph to search for nodes.
            node_type (str): The type of nodes to retrieve.

        Returns:
            List: A list of node IDs that have the specified type.
        """
        return [node_id for node_id, node_data in G.nodes(data=True) if node_data['type'] == node_type]
    
    @staticmethod
    def get_nodes_by_types(G: nx.MultiDiGraph, node_types: list):
        """
        Returns a generator that yields nodes from the given graph `G` based on the specified `node_types`.

        Parameters:
            G (nx.MultiDiGraph): The graph to search for nodes.
            node_types (list): A list of node types to filter the nodes.

        Yields:
            node: A node from the graph that matches one of the specified node types.
        """
        for node_type in node_types:
            yield from GraphVisitor.get_nodes_by_type(G, node_type)
            
    @staticmethod
    def find_nodes_by_type_from_source(G: nx.MultiDiGraph, source_node: str, target_type: str):
        """
        Find all nodes by type starting from a source node and traversing all subsequent child nodes.

        Parameters:
            G (nx.MultiDiGraph): The graph to search in.
            source_node (str): The starting node.
            target_type (str): The type of the nodes to find.

        Returns:
            List[str]: A list of IDs of the nodes with the specified type.
        """
        visited = set()
        queue = deque([source_node])
        result = []

        while queue:
            current_node = queue.popleft()
            if current_node in visited:
                continue
            visited.add(current_node)

            if G.nodes[current_node]['type'] == target_type:
                result.append(current_node)

            for successor in G.successors(current_node):
                if successor not in visited:
                    queue.append(successor)

        return result
    
    @staticmethod
    def generate_subgraph(G: nx.MultiDiGraph, start_node, edge_type = EdgeType.AST):
        """
        Generate a subgraph of the symbols graph based on the edge type and direction.

        Parameters:
        - node (int): Node to start the subgraph from.
        - edge_type (str): Type of the edge to consider.

        Returns:
        - subgraph (nx.MultiDiGraph): Subgraph of the symbols graph.
        """
        subgraph = nx.MultiDiGraph()
        
        for u, v in NXAlgorithms.get_subsequent_successors(G, start_node, edge_type):
            subgraph.add_node(u, **G.nodes[u])
            subgraph.add_node(v, **G.nodes[v])
            if GraphVisitor.check_edge(G, u, v, type=edge_type):
                subgraph.add_edge(u, v, key=edge_type, **G.edges[u, v, edge_type])
                
        return subgraph
    
    @staticmethod
    def check_edge(G: nx.MultiDiGraph, u, v, type=EdgeType.AST):
        """
        Check if an edge exists between two nodes in a MultiDiGraph.

        Parameters:
        - G (nx.MultiDiGraph): The graph to search in.
        - u (str): The source node.
        - v (str): The target node.
        - type (str): The type of the edge to check.

        Returns:
        - bool: True if the edge exists, False otherwise.
        """
        return G.has_edge(u, v, key=type)
    
    @staticmethod
    def get_outdegree_edges_by_type(G: nx.MultiDiGraph, node: str, edge_type: str):
        """
        Get the outdegree edges from a node filtered by edge type.

        Parameters:
            G (nx.MultiDiGraph): The graph to search in.
            node (str): The node to get the outdegree edges from.
            edge_type (str): The type of edges to filter by.

        Returns:
            List[Tuple[str, str, str]]: A list of tuples representing the edges (source, target, edge_type).
        """
        return [(u, v, k) for u, v, k in G.out_edges(node, keys=True) if k == edge_type]

    @staticmethod
    def get_indegree_edges_by_type(G: nx.MultiDiGraph, node: str, edge_type: str):
        """
        Get the indegree edges to a node filtered by edge type.

        Parameters:
            G (nx.MultiDiGraph): The graph to search in.
            node (str): The node to get the indegree edges to.
            edge_type (str): The type of edges to filter by.

        Returns:
            List[Tuple[str, str, str]]: A list of tuples representing the edges (source, target, edge_type).
        """
        return [(u, v, k) for u, v, k in G.in_edges(node, keys=True) if k == edge_type]
    
    @staticmethod
    def immediate_successors(G: nx.MultiDiGraph, node: str, filter_by_type: list=None, sort=False):
        """
        Returns an iterator that yields the immediate successors of a given node in a directed graph.

        Parameters:
            G (nx.MultiDiGraph): The directed graph.
            node(str): The node for which to find the immediate successors.
            filter_by_type (list): A list of node types to filter the successors.
            sort (bool): Whether to sort the successors based on a specific criteria.

        Yields:
            successor: The immediate successor of the given node.
        """
        successors = G.successors(node)
        
        if filter_by_type:
            successors = [s for s in successors if G.nodes[s]['type'] in filter_by_type]
        
        if sort:
            successors = sorted(successors, key=lambda s: G.nodes[s]['src_bytes_range'][0])
        
        for successor in successors:
            yield successor

    @staticmethod
    def immediate_predecessors(G: nx.MultiDiGraph, node: str, filter_by_type: list=None, sort=False):
        """
        Returns an iterator that yields the immediate predecessors of a given node in a directed graph.

        Parameters:
            G (nx.MultiDiGraph): The directed graph.
            node(str): The node for which to find the immediate predecessors.
            filter_by_type (list): A list of node types to filter the predecessors.
            sort (bool): Whether to sort the predecessors based on a specific criteria.

        Yields:
            predecessor: The immediate predecessor of the given node.
        """
        predecessors = G.predecessors(node)
        
        if filter_by_type:
            predecessors = [p for p in predecessors if G.nodes[p]['type'] in filter_by_type]
        
        if sort:
            predecessors = sorted(predecessors, key=lambda p: G.nodes[p]['src_bytes_range'][0])
        
        for predecessor in predecessors:
            yield predecessor

    @staticmethod
    def walk_nodes_by_edge_type(G: nx.MultiDiGraph, source_node: str, edge_type: str):
        """
        Walk the control flow graph starting from a given node.
        
        Parameters:
        - G: nx.MultiDiGraph - The control flow graph.
        - node - The starting node.
        - inward_walk: bool - (Default 'True') - Flag indicating whether to walk inward or outward in the control flow graph.
        
        Yields:
        - current_node - The current node being visited.
        - successors/predecessors - The successors or predecessors of the current node, depending on the value of inward_walk.
        """
        for current_node, successors, delayed_nodes in NXAlgorithms.dfs_successors_by_edge_property(G, source_node, edge_type):
            yield current_node, successors, delayed_nodes
             
class GraphTreeVisitor:
    
    @staticmethod
    def get_import_pairs(G: nx.MultiDiGraph, node: str) -> list[tuple[str, str, str]]:
        """
        Get the import pairs from an import node in the graph.

        Parameters:
            G (nx.MultiDiGraph): The graph to search in.
            node (str): The import node.

        Returns:
            list[tuple[str, str, str]]: A list of tuples representing the import pairs.
        """
        node_type = G.nodes[node]['type']
        import_pairs = []
        
        if node_type == TSNodeGroup.IMPORT_STMT:
            for child in GraphVisitor.get_children_by_field_name(G, node, 'name'):
                child_type = G.nodes[child]['type']
                
                if child_type == TSNodeGroup.DOTTED_NAME:
                    import_pairs.append((child, None, None))
                elif child_type == TSNodeGroup.ALIASED_IMPORT:
                    alias = GraphVisitor.get_child_by_field_name(G, child, 'alias')
                    n_dotted_name = GraphVisitor.get_child_by_field_name(G, child, 'name')
                    import_pairs.append((n_dotted_name, None, alias))
                
        elif node_type == TSNodeGroup.IMPORT_FROM_STMT:
            module_name = GraphVisitor.get_child_by_field_name(G, node, 'module_name')
            
            for child in GraphVisitor.get_children_by_field_name(G, node, 'name'):
                child_type = G.nodes[child]['type']
                
                if child_type == TSNodeGroup.DOTTED_NAME:
                    import_pairs.append((module_name, child, None))
                elif child_type == TSNodeGroup.ALIASED_IMPORT:
                    alias = GraphVisitor.get_child_by_field_name(G, child, 'alias')
                    n_dotted_name = GraphVisitor.get_child_by_field_name(G, child, 'name')
                    import_pairs.append((module_name, n_dotted_name, alias))
                    
            wildcard = GraphVisitor.get_child_by_type(G, node, TSNodeGroup.WILDCARD_IMPORT)
            if wildcard:
                import_pairs.append((module_name, wildcard, None))
            
                
        return import_pairs
    
    @staticmethod
    def assignment_pairs(G: nx.MultiDiGraph, node: str):
        """
        Get the identifier assignment pairs from an assignment node in the graph.

        Parameters:
            G (nx.MultiDiGraph): The graph to search in.
            node (str): The assignment node.

        Returns:
            List[Tuple]: A list of (lhs, rhs) pairs from the assignment node.
        """
        lhs = GraphVisitor.get_child_by_field_name(G, node, 'left')
        rhs = GraphVisitor.get_child_by_field_name(G, node, 'right')
        
        if lhs is None or rhs is None:
            return []
        
        lhs_type = G.nodes[lhs].get('type')
        rhs_type = G.nodes[rhs].get('type')
        
        if lhs_type == TSNodeGroup.PATTERN_LIST and rhs_type == TSNodeGroup.EXPR_LIST:
            lhs_elements = GraphVisitor.immediate_successors(G, lhs)
            rhs_elements = GraphVisitor.immediate_successors(G, rhs)
            return list(zip(lhs_elements, rhs_elements))
        
        return [(lhs, rhs)]
    
    @staticmethod
    def argument_pairs(G: nx.MultiDiGraph, call_node: str):
        """
        Get the argument pairs from an argument list node in the graph.

        Parameters:
            G (nx.MultiDiGraph): The graph to search in.
            node (str): The argument list node.

        Returns:
            List[Tuple]: A list of (parameter, argument) pairs from the argument list node.
        """
        arg_pairs = []
        
        arg_list = GraphVisitor.get_child_by_field_name(G, call_node, 'arguments')
        for arg in GraphVisitor.immediate_successors(G, arg_list):
            arg_type = GraphVisitor.get_node_by_id(G, arg).get('type')
            
            if arg_type == TSNodeGroup.KEYWORD_ARG:
                parameter = GraphVisitor.get_child_by_field_name(G, arg, 'name')
                argument = GraphVisitor.get_child_by_field_name(G, arg, 'value')
                arg_pairs.append((parameter, argument))
            elif arg_type in TSNodeGroup.STANDALONE_ASGMT_RIGHT:
                arg_pairs.append((None, arg))
            
        return arg_pairs
    
    @staticmethod
    def unnamed_arg_pair_count(pais: list[tuple[str, str]]):
        """
        Count the number of unnamed argument pairs in a list of argument pairs.

        Parameters:
            pairs (list[tuple[str, str]]): A list of argument pairs.

        Returns:
            int: The number of unnamed argument pairs.
        """
        return sum(1 for param, _ in pais if param is None)
    
    @staticmethod
    def get_identifier_list(G: nx.MultiDiGraph, node: str):
        """
        Get the list of identifiers from an identifier list node in the graph.

        Parameters:
            G (nx.MultiDiGraph): The graph to search in.
            node (str): The identifier list node.

        Returns:
            List[str]: A list of identifiers from the identifier list node.
        """
        return list(GraphVisitor.immediate_successors(G, node, filter_by_type=[TSNodeGroup.IDENTIFIER]))
            
    @staticmethod
    def get_object_attribute_sequence(G: nx.MultiDiGraph, attribute_node: str):
        """
        Get the sequence of object attributes from an object attribute node in the graph.

        Parameters:
            G (nx.MultiDiGraph): The graph to search in.
            node (str): The object attribute node.

        Returns:
            List[str]: A list of object attributes from the object attribute node.
        """
        object_node = None
        attribute_nodes = []
        
        for child in GraphVisitor.immediate_successors(G, attribute_node):
            child_type = G.nodes[child].get('type')
            child_field_name = G.nodes[child].get('field_name')
            
            if child_field_name == TSNodeGroup.FIELD_OBJECT:
                object_node = child
            elif child_field_name == TSNodeGroup.ATTRIBUTE:
                attribute_nodes.append(child)
                
            if child_type == TSNodeGroup.ATTRIBUTE:
                child_object_node, child_attribute_node = GraphTreeVisitor.get_object_attribute_sequence(G, attribute_node=child)
                object_node = child_object_node
                attribute_nodes.extend(child_attribute_node)
        
        return object_node, attribute_nodes
    
class NXAlgorithms:
    
    @staticmethod
    def topological_sort(G: nx.MultiDiGraph):
        """
        Resolve the order of nodes in the symbols graph based on the edge type.

        Parameters:
        - edge_type (str): Type of the edge to consider.

        Yield:
        - order (list): List of nodes in the resolved order.
        """     
        return list(reversed(list(nx.topological_sort(G))))
    
    @staticmethod
    def get_successors(G: nx.MultiDiGraph, node, edge_type=EdgeType.AST):
        """
        Get successors of a given node by a specific edge type in a NetworkX MultiDiGraph.

        Parameters:
        G (nx.MultiDiGraph): The graph.
        node: The node for which to find successors.
        edge_type: The type of edge to filter by.

        Returns:
        list: A list of successor nodes.
        """
        successors = []
        for succ in G.successors(node):
            # Check all edges between node and succ
            edges = G.get_edge_data(node, succ)
            for key in edges.keys():
                if key == edge_type:
                    successors.append(succ)
                    break  # No need to check other edges if one matches the type
                
        return successors
    
    @staticmethod
    def get_subsequent_successors(G: nx.MultiDiGraph, node, edge_type, visited=None):
        """
        Get all successors recursively of a given node by a specific edge type in a NetworkX MultiDiGraph.

        Parameters:
        G (nx.MultiDiGraph): The graph.
        node: The node for which to find successors.
        edge_type: The type of edge to filter by.
        visited (set): A set to keep track of visited nodes. (optional)

        Yields:
        The successor nodes.
        """
        if visited is None:
            visited = set()
        
        if node not in visited:
            visited.add(node)
            for succ in NXAlgorithms.get_successors(G, node, edge_type):
                yield (node, succ)
                yield from NXAlgorithms.get_subsequent_successors(G, succ, edge_type, visited)
    
    @staticmethod
    def bfs_successors_by_edge_property(G: nx.MultiDiGraph, source, edge_type):
        """
        Perform a breadth-first search (BFS) to find successors in a NetworkX MultiDiGraph
        based on a specific edge property.

        :param G: The NetworkX MultiDiGraph.
        :param source: The source node to start the BFS.
        :param edge_type: Edge type.
        :yield: Tuples of (current_node, list_of_successors) for each matching edge.
        """
        visited = set()
        queue = deque([source])
        successors = defaultdict(list)
        
        while queue:
            current_node = queue.popleft()
            visited.add(current_node)
            
            for _, successor, e_type in G.out_edges(current_node, keys=True):
                if e_type == edge_type and successor not in visited:
                    successors[current_node].append(successor)
                    if successor not in queue:
                        queue.append(successor)
                        visited.add(successor)
            
            if successors[current_node]:
                yield (current_node, successors[current_node])
    
    @staticmethod
    def dfs_successors_by_edge_property(G: nx.MultiDiGraph, source, edge_type):
        """
        Perform a depth-first search (DFS) to find successors in a NetworkX MultiDiGraph
        based on a specific edge property. Ensures that nodes with multiple in-degrees 
        are fully explored only after all their predecessors are explored.
        
        :param G: The NetworkX MultiDiGraph.
        :param source: The source node to start the DFS.
        :param edge_type: The edge type to filter by.
        :yield: Tuples of (current_node, list_of_successors, delayed_nodes) for each matching edge.
        """
        visited = set()
        stack = [source]
        delayed_nodes = {}  # Keep track of nodes with multiple predecessors

        while stack:
            current_node = stack.pop()

            ## Filter in-edges based on edge_type and count them
            in_edges_with_type = [
                (pred, edge_key) for pred, _, edge_key in G.in_edges(current_node, keys=True)
                if edge_key == edge_type
            ]
            in_degree = len(in_edges_with_type)
            
            if in_degree > 1 and current_node not in visited:
                # Delay visiting this node until all predecessors are visited
                if any(pred not in visited for pred, _ in in_edges_with_type):
                    delayed_nodes[current_node] = True
                    continue

            if current_node not in visited:
                visited.add(current_node)
                
                # Gather all successors based on the edge_type
                successors = []
                for _, successor, e_type in G.out_edges(current_node, keys=True):
                    if e_type == edge_type:
                        successors.append(successor)
                
                # Yield the current node, its successors, and the delayed nodes
                yield current_node, successors, list(delayed_nodes.keys())

                # Add successors to the stack (in reverse order to maintain DFS behavior)
                for successor in reversed(successors):
                    if successor not in visited:
                        stack.append(successor)

            # Reprocess delayed nodes if their predecessors are fully visited
            for delayed_node in list(delayed_nodes):
                # Recheck predecessors with the given edge_type
                in_edges_for_delayed = [
                    (pred, edge_key) for pred, _, edge_key in G.in_edges(delayed_node, keys=True)
                    if edge_key == edge_type
                ]
                if all(pred in visited for pred, _ in in_edges_for_delayed):
                    stack.append(delayed_node)
                    del delayed_nodes[delayed_node]
