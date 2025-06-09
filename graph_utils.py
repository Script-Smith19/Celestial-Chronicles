from collections import defaultdict, deque

def toposort(graph_dict):
    """
    Performs a topological sort on a dependency graph.

    graph_dict: dict[str, list[str]]
        A mapping from node -> list of parents (dependencies).
    Returns:
        A list of nodes in topologically sorted order.
    """
    graph = defaultdict(list)
    in_degree = defaultdict(int)

    # Collect all nodes
    for node, parents in graph_dict.items():
        in_degree[node] = 0  # Ensure all nodes are included

    # Build graph and in-degree map
    for node, parents in graph_dict.items():
        for parent in parents:
            if parent:
                graph[parent].append(node)
                in_degree[node] += 1

    queue = deque([name for name, deg in in_degree.items() if deg == 0])
    sorted_nodes = []

    while queue:
        current = queue.popleft()
        sorted_nodes.append(current)
        for child in graph[current]:
            in_degree[child] -= 1
            if in_degree[child] == 0:
                queue.append(child)

    if len(sorted_nodes) != len(in_degree):
        raise ValueError("Cycle detected in dependencies!")

    return sorted_nodes


def build_reverse_graph(graph_dict):
    """
    Builds the reverse of a dependency graph.

    graph_dict: dict[str, list[str]]
        A mapping from node -> list of parents (dependencies).
    Returns:
        dict[str, list[str]]: node -> list of children
    """
    reverse_graph = defaultdict(list)

    for node, parents in graph_dict.items():
        for parent in parents:
            if parent:
                reverse_graph[parent].append(node)

    return reverse_graph


def get_all_descendants(start, reverse_graph):
    """
    Returns all descendants (transitive children) of a node.

    start: str
        The starting node.
    reverse_graph: dict[str, list[str]]
        The reverse dependency graph (node -> list of children).
    Returns:
        set[str]: All reachable descendants from `start`.
    """
    descendants = set()
    queue = deque([start])

    while queue:
        current = queue.popleft()
        for child in reverse_graph.get(current, []):
            if child not in descendants:
                descendants.add(child)
                queue.append(child)

    return descendants