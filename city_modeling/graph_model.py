
class GraphModel:
    def __init__(self):
        self.nodes = {}
        self.edges = {}

    def add_node(self, node_id, node_data):
        """Add an intersection to the graph."""
        self.nodes[node_id] = node_data

    def remove_node(self, node_id):
        """Remove an intersection from the graph."""
        if node_id in self.nodes:
            del self.nodes[node_id]

            self.edges = {k: v for k, v in self.edges.items() if k[0] != node_id and k[1] != node_id}

    def add_edge(self, node1_id, node2_id, edge_data):
        """Add a road between two intersections."""
        self.edges[(node1_id, node2_id)] = edge_data

    def remove_edge(self, node1_id, node2_id):
        """Remove a road between two intersections."""
        if (node1_id, node2_id) in self.edges:
            del self.edges[(node1_id, node2_id)]

    def find_shortest_path(self, start_node, end_node):
        """Implement shortest path finding algorithm here (e.g., Dijkstra or A*)."""
        pass
