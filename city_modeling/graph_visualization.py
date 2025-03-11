import networkx as nx
import matplotlib.pyplot as plt

class GraphVisualization:
    def __init__(self, graph_model):
        """
        Initializes the GraphVisualization object with a graph model.
        The graph model should be an instance of NetworkXGraph.
        """
        self.graph_model = graph_model

    def draw_city_graph(self):
        """Visualizes the city graph using NetworkX and Matplotlib."""
        G = self.graph_model.get_graph()
        pos = nx.get_node_attributes(G, 'pos')
    
        plt.figure(figsize=(8, 8))
        nx.draw(G, pos, with_labels=True, node_size=300,
                node_color='lightblue', edge_color='gray',
                arrows=True, arrowsize=15)
        plt.title("Generated City Graph")
        plt.show()