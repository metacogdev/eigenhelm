def topological_sort(graph):
    """Kahn's algorithm for topological sort.

    Args:
        graph: dict mapping node to list of dependencies (edges point to).

    Returns:
        List of nodes in topological order, or None if cycle detected.
    """
    in_degree = {}
    for node in graph:
        in_degree.setdefault(node, 0)
        for neighbor in graph[node]:
            in_degree[neighbor] = in_degree.get(neighbor, 0) + 1

    queue = [n for n in in_degree if in_degree[n] == 0]
    result = []

    while queue:
        node = queue.pop(0)
        result.append(node)
        for neighbor in graph.get(node, []):
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)

    if len(result) != len(in_degree):
        return None  # Cycle detected
    return result
