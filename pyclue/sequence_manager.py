class Node:
    def __init__(self, id: str):
        if not isinstance(id, str):
            raise TypeError("id must be a string")
        self.id: str = id

class Sequence:
    def __init__(self):
        self.items = []
        self.edges = []
        
    def has_items(self):
        return len(self.items) > 0
    
    def add_item(self, item):
        self.items.append(item)
                    
    def add_at_start(self, item):
        self.items.insert(0, item)
        
    def add_at_end(self, item):
        self.items.append(item)
        
    def get_head(self):
        if self.items:
            return self._get_item_head(self.items[0])
        return None
    
    def get_tail(self):
        if self.items:
            return self._get_item_tail(self.items[-1])
        return None
    
    def extend_sequence(self, other_sequence_items: list):
        self.items.extend(other_sequence_items)
    
    def generate_edges(self, edge_type):
        if len(self.items) == 0:
            return
        elif len(self.items) == 1:
            self.generate_edges_for_complex_sequence(self.items[0], edge_type)
        elif len(self.items) > 1:
            for i in range(len(self.items) - 1):
                tails = self._get_item_tail(self.items[i])
                head = self._get_item_head(self.items[i + 1])
                self.generate_edges_for_complex_sequence(self.items[i + 1], edge_type)
                
                if head and tails:
                    if len(tails) > 0:
                        for tail in tails:
                            self.edges.append((tail.id, head.id, edge_type))
                    
                    
    def generate_edges_for_complex_sequence(self, item, edge_type):
         if isinstance(item, LoopSequence) or isinstance(item, ConditionalSequence) or isinstance(item, ExceptionSequence):
            self.edges.extend(item.generate_edges(edge_type))
            
    def _get_item_head(self, item):
        head = None
        if type(item) is Node:
            head = item
        elif type(item) is Sequence:
            head = item.get_head()
        elif type(item) is LoopSequence:
            head = item.main_s.get_head()
        elif type(item) is ConditionalSequence:
            if item.sequences:
                head = Node(list(item.sequences.keys())[0])
        elif type(item) is ExceptionSequence:
            head = item.try_s.get_head()
        
        return head
    
    def _get_item_tail(self, item):
        tails = []
        
        if type(item) is Node:
            tails.append(item)
        elif type(item) is Sequence:
            tails.append(item.get_tail())
        elif type(item) is LoopSequence:
            tails = item.main_s.get_tail()
        elif type(item) is ConditionalSequence:
            for key, sequence in item.sequences.items():
                tails.extend(sequence.get_tail())
        elif type(item) is ExceptionSequence:
            if item.finally_s.has_items():
                tails = item.finally_s.get_tail()
            else:
                tails: list = item.try_s.get_tail()
                for key, sequence in item.except_ss.items():
                    tails.extend(sequence.get_tail())
        
        return tails
        
class ConditionalSequence(Sequence):
    """
    Manage multiple sequences in a graph, like a jagged sequence
    """
    def __init__(self):
        self.sequences: dict[str, Sequence] = {}
        super().__init__()
        
    def add_sequence(self, key, sequence: Sequence):
        self.sequences[key] = sequence
    
    def generate_edges(self, edge_type):
        edges = []
        main_s = Sequence()
        
        for key, sequence in self.sequences.items():
            if key == "else":
                main_s.add_item(sequence.get_head())
            else:
                main_s.add_item(Node(key))
                if sequence.get_head():
                    edges.append((key, sequence.get_head().id, edge_type))
            
            sequence.generate_edges(edge_type)
            edges.extend(sequence.edges)
            
        main_s.generate_edges(edge_type)
        edges.extend(main_s.edges)
        return edges
    
class LoopSequence(Sequence):
    def __init__(self):
        self.main_s = Sequence()
        self.block_s = Sequence()
        self.left_id = None
        super().__init__()
        
    def generate_edges(self, edge_type):
        edges = []
        
        self.block_s.generate_edges(edge_type)
        edges.extend(self.block_s.edges)
        
        if self.left_id:
            if self.block_s.get_head():
                edges.append((self.left_id, self.block_s.get_head().id, edge_type))
            if self.block_s.get_tail():
                for tail_node in self.block_s.get_tail():
                    edges.append((tail_node.id, self.left_id, edge_type))
                    
        return edges
        
class ExceptionSequence(Sequence):
    def __init__(self):
        self.try_s = Sequence()
        self.except_ss: dict[str, Sequence] = {}
        self.finally_s = Sequence()
        super().__init__()
        
    def add_except_sequence(self, key, sequence: Sequence):
        self.except_ss[key] = sequence
        
    def generate_edges(self, edge_type):
        edges = []
        
        self.try_s.generate_edges(edge_type)
        edges.extend(self.try_s.edges)
        
        except_head, except_edges = self._generate_except_sequences_edges(edge_type)
        edges.extend(except_edges)
        
        for tail in self.try_s.get_tail():
            if except_head:
                edges.append((tail.id, except_head.id, edge_type))
        
        if self.finally_s.has_items():
            self.finally_s.generate_edges(edge_type)
            edges.extend(self.finally_s.edges)
            
            for tail in self.try_s.get_tail():
                if self.finally_s.get_head():
                    edges.append((tail.id, self.finally_s.get_head().id, edge_type))
                    
            for key, sequence in self.except_ss.items():
                for tail in sequence.get_tail():
                    edges.append((tail.id, self.finally_s.get_head().id, edge_type))
                    
        return edges
    
    def _generate_except_sequences_edges(self, edge_type):
        edges = []
        head = None
        main_s = Sequence()
        
        for key, sequence in self.except_ss.items():
            if key == "except":
                main_s.add_item(sequence.get_head())
            else:
                main_s.add_item(Node(key))
                if sequence.get_head():
                    edges.append((key, sequence.get_head().id, edge_type))
            
            sequence.generate_edges(edge_type)
            edges.extend(sequence.edges)
            
        main_s.generate_edges(edge_type)
        edges.extend(main_s.edges)
        
        head = main_s.get_head()
        
        return head, edges