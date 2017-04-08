from graphviz import Digraph

import task_definitions

graph = Digraph('dependencies', format='svg')

for v in vars(task_definitions).values():
    if isinstance(v, type) and v != task_definitions.TaskDefinition and issubclass(v, task_definitions.TaskDefinition):
        graph.node(v.__name__)
        if hasattr(v, 'dependencies'):
            for dependency in v.dependencies:
                graph.edge(dependency.__name__, v.__name__)

graph.render('dependencies', cleanup=True)
