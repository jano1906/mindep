import ast
from argparse import ArgumentParser
from dataclasses import dataclass
from typing import List, Optional, Set
from abc import ABC

def get_parser():
    parser = ArgumentParser()
    parser.add_argument("--file", type=str, required=True)
    parser.add_argument("--function", type=str, required=True)
    return parser

@dataclass
class FInfo:
    name: str
    begin: int
    end: int
    deps: Optional[Set[str]] #None iff unresolved

class DependencyResolver(ABC):
    def __init__(self, dependencies = set(), known_symbols = set()):
        self.dependencies: Set[str] = dependencies
        self.known_symbols: Set[str] = known_symbols
        self.tmp_symbols: Set[str] = set()

    def is_known(self, name: str):
        return name in self.known_symbols or name in self.tmp_symbols
    
    def get_dependencies(self):
        return self.dependencies.copy()

class ExprDependencyResolver(DependencyResolver):
    def add_expr_dependencies(self, exp: ast.expr):
        if isinstance(exp, ast.BoolOp):
            for e in exp.values:
                self.add_expr_dependencies(e)
        elif isinstance(exp, ast.NamedExpr):
            self.add_expr_dependencies(exp.value)
        elif isinstance(exp, ast.BinOp):
            self.add_expr_dependencies(exp.left)
            self.add_expr_dependencies(exp.right)
        elif isinstance(exp, ast.UnaryOp):
            self.add_expr_dependencies(exp.operand)
        elif isinstance(exp, ast.Lambda):
            self.add_expr_dependencies(exp.body)
        elif isinstance(exp, ast.IfExp):
            self.add_expr_dependencies(exp.test)
            self.add_expr_dependencies(exp.body)
            self.tmp_symbols.clear()
            self.add_expr_dependencies(exp.orelse)
        elif isinstance(exp, ast.Dict):
            for e in exp.values:
                self.add_expr_dependencies(e)
        elif isinstance(exp, ast.Set):
            for e in exp.elts:
                self.add_expr_dependencies(e)
        elif isinstance(exp, ast.ListComp):
            assert False
        elif isinstance(exp, ast.SetComp):
            assert False
        elif isinstance(exp, ast.DictComp):
            assert False
        elif isinstance(exp, ast.GeneratorExp):
            assert False
        elif isinstance(exp, ast.Await):
            assert False
        elif isinstance(exp, ast.Yield):
            assert False
        elif isinstance(exp, ast.YieldFrom):
            assert False
        elif isinstance(exp, ast.Compare):
            assert False
        elif isinstance(exp, ast.Call):
            assert False
        elif isinstance(exp, ast.FormattedValue):
            assert False
        elif isinstance(exp, ast.JoinedStr):
            assert False
        elif isinstance(exp, ast.Constant):
            pass
        elif isinstance(exp, ast.Attribute):
            assert False
        elif isinstance(exp, ast.Subscript):
            assert False
        elif isinstance(exp, ast.Starred):
            assert False
        elif isinstance(exp, ast.Name):
            if not self.is_known(exp.id):
                self.dependencies.add(exp.id)
        elif isinstance(exp, ast.List):
            assert False
        elif isinstance(exp, ast.Tuple):
            assert False
        elif isinstance(exp, ast.Slice):
            assert False

        if isinstance(exp, ast.NamedExpr):
            self.tmp_symbols.add(exp.target.id)
        else:
            self.tmp_symbols.clear()

class StmtDependencyResolver(DependencyResolver):
    def __init__(self, dependencies=set(), known_symbols=set()):
        super().__init__(dependencies, known_symbols)
        self.expr_resolver = ExprDependencyResolver(dependencies=self.dependencies, known_symbols=self.known_symbols)

    def add_stmt_dependencies(self, stmt: ast.stmt):
        def add_expr_dependencies(expr: ast.expr):
            self.tmp_symbols.difference_update(self.known_symbols)
            self.known_symbols.update(self.tmp_symbols)
            self.expr_resolver.add_expr_dependencies(expr)
            self.known_symbols.difference_update(self.tmp_symbols)
            
        if isinstance(stmt, ast.FunctionDef):
            self.dependencies.update(resolve_fdef(stmt, self.dependencies, self.known_symbols.copy()))
            self.known_symbols.add(stmt.name)

        elif isinstance(stmt, ast.AsyncFunctionDef):
            assert False
        elif isinstance(stmt, ast.ClassDef):
            self.known_symbols.update(stmt.name)
        elif isinstance(stmt, ast.Return):
            add_expr_dependencies(stmt.value)
        elif isinstance(stmt, ast.Delete):
            assert False
        elif isinstance(stmt, ast.Assign):
            add_expr_dependencies(stmt.value)
            self.known_symbols.update([t.id for t in stmt.targets])
        elif isinstance(stmt, ast.AugAssign):
            add_expr_dependencies(stmt.value)
            self.known_symbols.update(stmt.target)
        elif isinstance(stmt, ast.AnnAssign):
            if stmt.value is not None:
                add_expr_dependencies(stmt.value)
                self.known_symbols.update(stmt.target)
        elif isinstance(stmt, ast.For):
            assert isinstance(stmt.target, ast.Name)
            self.tmp_symbols.add(stmt.target.id)
            add_expr_dependencies(stmt.iter)
            for s in stmt.body:
                self.add_stmt_dependencies(s)
            self.tmp_symbols.remove(stmt.target.id)

class FDefDependencyResolver(DependencyResolver):
    def __init__(self, dependencies=set(), known_symbols=set()):
        super().__init__(dependencies=dependencies, known_symbols=known_symbols)
        self.stmt_resolver = StmtDependencyResolver(dependencies=self.dependencies, known_symbols=self.known_symbols)
    
    @staticmethod
    def get_args_symbols(args: ast.arguments) -> List[str]:
        args_symbols = []
        args_symbols += [a.arg for a in args.posonlyargs]
        args_symbols += [a.arg for a in args.args]
        args_symbols += [args.vararg.arg] if args.vararg is not None else []
        args_symbols += [a.arg for a in args.kwonlyargs]
        args_symbols += [args.kwarg.arg] if args.kwarg is not None else []
        return args_symbols
    
    def add_fdef_dependencies(self, fdef: ast.FunctionDef):
        self.known_symbols.update(self.get_args_symbols(fdef.args))
        self.known_symbols.add(fdef.name)
        for stmt in fdef.body:
            self.stmt_resolver.add_stmt_dependencies(stmt)

def resolve_fdef(fdef, dependencies=set(), known_symbols=set()):
    resolver = FDefDependencyResolver(dependencies=dependencies, known_symbols=known_symbols)
    resolver.add_fdef_dependencies(fdef)
    ret = resolver.get_dependencies()
    del resolver
    return ret

def main(args):
    file_name = args.file
    function_name = args.function
    with open(file_name) as f:
        src = f.read()
    tree = ast.parse(src)
    for stmt in tree.body:
        if isinstance(stmt, ast.FunctionDef):
            if stmt.name == function_name:
                deps = resolve_fdef(stmt)
                print(deps)
def dummy(main):
    for x in y:
        a = x
        b = t
    y = a
    return
    
if __name__ == "__main__":
    parser = get_parser()
    args = parser.parse_args()
    main(args)