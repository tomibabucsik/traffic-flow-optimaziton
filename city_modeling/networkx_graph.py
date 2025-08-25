import networkx as nx

class CityGraph:
    def __init__(self):
        self.graph = nx.DiGraph()

    def add_intersection(self, node_id, position):
        """Add an intersection (node)"""
        self.graph.add_node(node_id, pos=position)

    def add_road(self, start, end, length, speed_limit, lanes=1):
        """Add a road (edge) between intersections"""

        travel_time = (length / (speed_limit / 3.6))

        capacity = lanes * 1800

        self.graph.add_edge(
            start, end, 
            length=length,
            speed_limit=speed_limit,
            lanes=lanes,
            travel_time=travel_time,
            capacity=capacity,
            current_flow=0)

    def get_graph(self):
        return self.graph