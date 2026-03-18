import heapq


def dijkstra(graph, start):
    """Compute shortest distances from start using Dijkstra's algorithm.

    Args:
        graph: Adjacency list as dict[node, list[(neighbor, weight)]].
        start: Source node.

    Returns:
        dict mapping each reachable node to its shortest distance.
        Time: O((V + E) log V). Space: O(V).
    """
    distances = {start: 0}
    heap = [(0, start)]

    while heap:
        dist, node = heapq.heappop(heap)
        if dist > distances.get(node, float("inf")):
            continue
        for neighbor, weight in graph.get(node, []):
            new_dist = dist + weight
            if new_dist < distances.get(neighbor, float("inf")):
                distances[neighbor] = new_dist
                heapq.heappush(heap, (new_dist, neighbor))

    return distances
