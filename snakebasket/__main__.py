import ast
import os


class AstManipulator:
    """Used to manipulate the AST of a single source file."""

    def __init__(self, source: str, path: str) -> None:
        self.source = source
        self.path = path
        self.ast = None

    @classmethod
    def from_file(cls, filename: str, path: str) -> "AstManipulator":
        """Create a new instance using a file name."""
        with open(filename) as file:
            return cls(source=file.read(), path=path)

    def ensure_ast(self) -> None:
        """Make sure the ast attribute is populated."""
        if not self.ast:
            self.ast = ast.parse(self.source)

    def qualify_name(self, module: str, level: int) -> str:
        """Expand the dot aliases in the import names."""
        if not level:
            return module
        elif not module:
            return f"{'.'.join(self.path.split('.')[:-level])}"
        else:
            return f"{'.'.join(self.path.split('.')[:-level])}.{module.lstrip('.')}"

    def identify_dependencies(self) -> list[str]:
        """Gives a list of all the sub-dependencies of this file."""
        self.ensure_ast()

        dependencies = []

        for node in ast.walk(self.ast):
            if isinstance(node, ast.Import):
                dependencies.extend(alias.name for alias in node.names)
            if isinstance(node, ast.ImportFrom):
                qualified_name = self.qualify_name(node.module, node.level)

                dependencies.extend(f"{qualified_name}.{alias.name}" for alias in node.names)

        return dependencies


def walk_back_path(path: str) -> list[str]:
    """Returns every possible sub-path of the provided path, with and without __init__."""
    out = []
    parts = path.split(".")

    for i in range(1, len(parts) + 1):
        out.append(".".join(parts[:i]) + ".__init__")
        out.append(".".join(parts[:i]))

    return out


def graph_module(start_path: str) -> list[str]:
    """Identity all the files making up a specific module."""
    visited = set()
    detected = []
    to_visit = [start_path] + walk_back_path(start_path)

    while len(to_visit) > 0:
        path = to_visit.pop()

        # Skip paths we already visited
        if path in visited:
            continue
        visited.add(path)

        # TODO: Properly search for that file
        file = path.replace(".", "/") + ".py"
        if not os.path.exists(file):
            continue

        dependencies = AstManipulator.from_file(file, path).identify_dependencies()

        # We want to explore the dependency itself and any sub-path
        for dependency in dependencies:
            to_visit.append(dependency)
            to_visit.extend(walk_back_path(dependency))
        detected.append(file)
    return detected


print(graph_module("my_test.__main__"))
