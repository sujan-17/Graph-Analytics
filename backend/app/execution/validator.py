import ast

FORBIDDEN_MODULES = {
    "os", "sys", "subprocess", "socket", "requests", "urllib", "shutil", 
    "builtins", "__import__", "importlib", "pickle", "ctypes", "pathlib",
    "multiprocessing", "threading", "pty", "tempfile", "sqlite3", "inspect", "posix", "nt"
}

FORBIDDEN_BUILTINS = {
    "open", "eval", "exec", "__import__", "compile", "globals", "locals",
    "getattr", "setattr", "delattr", "hasattr", "input", "breakpoint", "memoryview"
}

FORBIDDEN_PANDAS_METHODS = {
    "to_csv", "to_excel", "to_json", "to_sql", "to_pickle", "to_parquet", "to_feather", "to_hdf",
    "to_stata", "to_clipboard", "read_csv", "read_sql", "read_excel", "read_parquet", "read_json",
    "read_table", "read_pickle", "read_feather", "read_hdf"
}

FORBIDDEN_ATTRIBUTES = {
    "__subclasses__", "__bases__", "__mro__", "__globals__", "__builtins__", "__code__"
}

class CodeValidator(ast.NodeVisitor):
    def __init__(self):
        self.errors = []

    def visit_Import(self, node):
        for alias in node.names:
            name = alias.name.split(".")[0]
            if name in FORBIDDEN_MODULES:
                self.errors.append(f"Forbidden import: '{alias.name}'")
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        if node.module:
            module_name = node.module.split(".")[0]
            if module_name in FORBIDDEN_MODULES:
                self.errors.append(f"Forbidden import from module: '{node.module}'")
        self.generic_visit(node)

    def visit_Attribute(self, node):
        if node.attr in FORBIDDEN_ATTRIBUTES:
            self.errors.append(f"Forbidden attribute access: '{node.attr}'")
        self.generic_visit(node)

    def visit_Call(self, node):
        if isinstance(node.func, ast.Name):
            if node.func.id in FORBIDDEN_BUILTINS:
                self.errors.append(f"Forbidden builtin function call: '{node.func.id}()'")
        elif isinstance(node.func, ast.Attribute):
            if node.func.attr in FORBIDDEN_PANDAS_METHODS:
                self.errors.append(f"Forbidden file I/O or export operation: '{node.func.attr}'")
        self.generic_visit(node)

def validate_code_ast(code: str) -> tuple[bool, list[str]]:
    """
    Parses generated Python code with AST and checks against safety security constraints.
    Returns (is_valid, list_of_error_messages).
    """
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return False, [f"Syntax Error: {e.msg} at line {e.lineno}"]

    validator = CodeValidator()
    validator.visit(tree)
    if validator.errors:
        return False, validator.errors
    return True, []
