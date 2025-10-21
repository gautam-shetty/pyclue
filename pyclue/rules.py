    
class TypeInferenceRules:
    
    @staticmethod
    def merge_types(types: list) -> str:
        unique_types = list(dict.fromkeys(types))
        unique_types = ['None' if t is None else t for t in unique_types]
        return ' | '.join(unique_types)

    @staticmethod
    def get_generic_type(generic_type: str, value_types, key_types) -> str:
        seen_key_type = set()
        if len(key_types) > 0:
            seen_key_type = [x for x in key_types if x is not None and x not in seen_key_type and not seen_key_type.add(x)]
        
        seen_value_type = set()
        if len(value_types) > 0:
            seen_value_type = [x for x in value_types if x is not None and x not in seen_value_type and not seen_value_type.add(x)]
            
        if seen_value_type:
            if seen_key_type:
                generic_type = f"{generic_type}[{' | '.join(seen_key_type)}, {' | '.join(seen_value_type)}]"
            else:
                generic_type = f"{generic_type}[{', '.join(seen_value_type)}]" 
        
        return generic_type
    
    @staticmethod
    def get_expr_type(left_type:str, operator:str, right_type:str) -> str:
        if left_type in ['true', 'false']:
            left_type ='bool'
        if right_type in ['true', 'false']:
            right_type ='bool'

        # Define rules for data type results based on operator types
        type_rules = {
            # Integer operations
            ('int', '+', 'int'): 'int',
            ('int', '-', 'int'): 'int',
            ('int', '*', 'int'): 'int',
            ('int', '/', 'int'): 'float',
            ('int', '//', 'int'): 'int',
            ('int', '%', 'int'): 'int',
            ('int', '**', 'int'): 'int',
            ('int', '==', 'int'): 'bool',
            ('int', '!=', 'int'): 'bool',
            ('int', '>', 'int'): 'bool',
            ('int', '<', 'int'): 'bool',
            ('int', '>=', 'int'): 'bool',
            ('int', '<=', 'int'): 'bool',
            ('int', 'and', 'int'): 'int',
            ('int', 'or', 'int'): 'int',
                
            # Float operations
            ('float', '+', 'float'): 'float',
            ('float', '-', 'float'): 'float',
            ('float', '*', 'float'): 'float',
            ('float', '/', 'float'): 'float',
            ('float', '**', 'float'): 'float',
            ('float', '==', 'float'): 'bool',
            ('float', '!=', 'float'): 'bool',
            ('float', '>', 'float'): 'bool',
            ('float', '<', 'float'): 'bool',
            ('float', '>=', 'float'): 'bool',
            ('float', '<=', 'float'): 'bool',
            ('float', 'and', 'float'): 'float',
            ('float', 'or', 'float'): 'float',
            
            # Boolean operations
            ('bool', 'and', 'bool'): 'bool',
            ('bool', 'or', 'bool'): 'bool',
            ('bool', '==', 'bool'): 'bool',
            ('bool', '!=', 'bool'): 'bool',
            
            # str operations
            ('str', '+', 'str'): 'str',
            ('str', '==', 'str'): 'bool',
            ('str', '!=', 'str'): 'bool',
            
            # Mixed operations
            ('int', '+', 'float'): 'float',
            ('float', '+', 'int'): 'float',
            ('int', '-', 'float'): 'float',
            ('float', '-', 'int'): 'float',
            ('int', '*', 'float'): 'float',
            ('float', '*', 'int'): 'float',
            ('int', '/', 'float'): 'float',
            ('float', '/', 'int'): 'float',
            ('int', '==', 'float'): 'bool',
            ('float', '==', 'int'): 'bool',
            ('int', '!=', 'float'): 'bool',
            ('float', '!=', 'int'): 'bool',
            ('int', '>', 'float'): 'bool',
            ('float', '>', 'int'): 'bool',
            ('int', '<', 'float'): 'bool',
            ('float', '<', 'int'): 'bool',
            ('int', '>=', 'float'): 'bool',
            ('float', '>=', 'int'): 'bool',
            ('int', '<=', 'float'): 'bool',
            ('float', '<=', 'int'): 'bool',
            ('str', '+', 'int'): 'str',
            ('int', '+', 'str'): 'str',
            ('str', '+', 'float'): 'str',
            ('float', '+', 'str'): 'str',
            ('str', '+', 'bool'): 'str',
            ('bool', '+', 'str'): 'str'
        }

        # Get the result type based on the provided left type, operator, and right type
        return type_rules.get((left_type, operator, right_type))