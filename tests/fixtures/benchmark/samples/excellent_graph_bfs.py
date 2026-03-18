from collections import deque


def bfs_shortest_path(graph, start, end):
    """Find shortest path in unweighted graph using BFS.

    Args:
        graph: Adjacency list as dict[node, list[node]].
        start: Source node.
        end: Target node.

    Returns:
        List of nodes forming shortest path, or empty list if unreachable.
        Time: O(V + E). Space: O(V).
    """
    if start == end:
        return [start]

    visited = {start}
    queue = deque([(start, [start])])

    while queue:
        current, path = queue.popleft()
        for neighbor in graph.get(current, []):
            if neighbor == end:
                return path + [neighbor]
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append((neighbor, path + [neighbor]))

    return []
