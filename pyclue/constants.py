import logging
from tree_sitter import Language
import tree_sitter_python as tspython

class AppConfig:
    SUPPORTED_FILE_EXTENSIONS = [".py"]
    IGNORE_DIRECTORIES = [".github", ".git", ".venv", "__pycache__"]
    
class AppLogger:
    LOGGING_LEVEL = logging.INFO
    LOGGING_FORMAT = "%(asctime)s-%(process)d [%(levelname)s] %(name)s: %(message)s"
    
    logging.basicConfig(
        level=LOGGING_LEVEL,
        format=LOGGING_FORMAT,
        handlers=[
            logging.StreamHandler()
        ]
    )
    
    @staticmethod
    def add_file_handler(log_file_path: str):
        file_handler = logging.FileHandler(log_file_path)
        file_handler.setLevel(AppLogger.LOGGING_LEVEL)
        file_handler.setFormatter(logging.Formatter(AppLogger.LOGGING_FORMAT))
        logging.getLogger().addHandler(file_handler)

class EdgeType:
    AST = "AST" # Abstract Syntax Tree
    CF = "CF" # Control Flow
    DF = "DF" # Data Flow

class TSLanguage:
    """
    tree-sitter languages library
    """
    PY_LANGUAGE = Language(tspython.language())
    
class TypePairs():
    """
    Type inference pairs
    """
    STR = "str"
    INT = "int"
    FLOAT = "float"
    BOOL = "bool"
    NONE_TYPE = "None"
    LIST = "list"
    DICT = "dict"
    SET = "set"
    TUPLE = "tuple"
    
    @staticmethod
    def covert_ts_to_py_type(ts_type: str):
        ts_types = {
            "string": TypePairs.STR,
            "integer": TypePairs.INT,
            "float": TypePairs.FLOAT,
            "true": TypePairs.BOOL,
            "false": TypePairs.BOOL,
            "none": TypePairs.NONE_TYPE,
            "list": TypePairs.LIST,
            "dictionary": TypePairs.DICT,
            "set": TypePairs.SET,
            "tuple": TypePairs.TUPLE,
        }
        
        return ts_types.get(ts_type, ts_type)

class TSNodeGroup():
    """
    tree-sitter node groups
    """
    FIELD_ATTRIBUTE = "attribute"
    FIELD_OBJECT = "object"
    
    MODULE = "module"
    BLOCK = "block"
    DUMMY = "dummy"
    COMMENT = "comment"
    
    IMPORT_STMT = "import_statement"
    IMPORT_FROM_STMT = "import_from_statement"
    WILDCARD_IMPORT = "wildcard_import"
    ALIASED_IMPORT = "aliased_import"
    IMPORTS = [IMPORT_STMT, IMPORT_FROM_STMT]
    
    IDENTIFIER = "identifier"
    ATTRIBUTE = "attribute"
    AS_PATTERN = "as_pattern"
    PATTERN_LIST = "pattern_list"
    EXPR_LIST = "expression_list"
    DOTTED_NAME = "dotted_name"
    
    CLS_NODE = "class_definition"
    
    FN_NODE = "function_definition"
    FN_PARAMS = "parameters"
    FN_DEFAULT_PARAM = "default_parameter"
    FN_TYPED_PARAM = "typed_parameter"
    FN_TYPED_DEFAULT_PARAM = "typed_default_parameter"
    FN_TYPED_RETURN = "return_type"
    
    FN_PARAM_BLOCK = [FN_TYPED_DEFAULT_PARAM, FN_DEFAULT_PARAM, FN_TYPED_PARAM, IDENTIFIER]
    
    CONDITIONAL_IF = "if_statement"
    CONDITIONAL_ELIF = "elif_clause"
    CONDITIONAL_ELSE = "else_clause"
    CONDITIONAL_ALTERNATIVE = [CONDITIONAL_ELIF, CONDITIONAL_ELSE]
    
    FOR_LOOP = "for_statement"
    WHILE_LOOP = "while_statement"
    LOOP = [FOR_LOOP, WHILE_LOOP]
    
    EXCEPTION_TRY = "try_statement"
    EXCEPTION_EXCEPT = "except_clause"
    EXCEPTION_FINALLY = "finally_clause"
    
    NODES_WITH_TEXT = ["type", WILDCARD_IMPORT, DOTTED_NAME, IDENTIFIER]
    NODES_WITH_TEXT_MASKED = ["string", "integer", "float"]
    NODES_WITH_DUMMY_NODE = [MODULE, CLS_NODE, FN_NODE]
    
    EXPR_STMT = "expression_statement"
    RETURN_STMT = "return_statement"
    ASGMT = "assignment"
    STANDALONE_ASGMT_RIGHT = [IDENTIFIER, "string", "integer", "float"]
    CALL = "call"
    KEYWORD_ARG = "keyword_argument"
    # USE_NODES = [EXPR_STMT, RETURN_STMT]
    DEF_NODES = [CLS_NODE, FN_NODE]
    DICT_PAIR = "pair"
    
    ELEMENTARY_TYPES = ["string", "integer", "float", "none", "true", "false"]
    GENERIC_TYPES = ["list", "dictionary", "set", "tuple"]
    OPERATOR_TYPES = ["binary_operator", "boolean_operator", "comparison_operator"]
    
    SYMBOLS = ["(", ")", "{", "}", "[", "]", ",", ":", "=", ".", "->"]
    NAMED_KEYWORDS = ["class", "def", 
                      "if", "elif", "else", 
                      "for", "while", "yield", 
                      "try", "except", "finally", "raise",
                      "import", "from", "as", 
                      "return", "pass", "break", "continue", "del",
                      "with", "global", "assert"]
    SKIP_NODES_BY_TYPE = set([COMMENT, "string_start", "string_content", "string_end"] + SYMBOLS + NAMED_KEYWORDS)
    
    
class DummyNode:
    START = "START"
    EXIT = "EXIT"
    ENTRY = "ENTRY"
    RETURN = "RETURN"
    
class TypeInfrnNodeGroup:
    """
    Type inference groups
    """
    STMTS_TYPES = [TSNodeGroup.EXPR_STMT, TSNodeGroup.RETURN_STMT]
