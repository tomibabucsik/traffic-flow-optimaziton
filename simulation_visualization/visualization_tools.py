import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import networkx as nx
import numpy as np
import matplotlib.animation as animation

def plot_traffic_snapshot(city_graph, vehicles, simulation=None):
    """Plot road network with vehicle distribution and traffic density"""
    G = city_graph.get_graph()
    pos = nx.get_node_attributes(G, 'pos')
    
    plt.figure(figsize=(12, 10))
    
    # Calculate edge colors based on congestion
    edge_colors = []
    edge_widths = []
    
    for u, v in G.edges():
        # Calculate congestion ratio
        flow = G[u][v]['current_flow']
        capacity = G[u][v]['capacity']
        ratio = flow / capacity if capacity > 0 else 0
        
        # Green (low traffic) to red (high traffic) color gradient
        if ratio < 0.5:
            color = (0, 1, 0)  # Green
        elif ratio < 0.8:
            color = (1, 1, 0)  # Yellow
        else:
            color = (1, 0, 0)  # Red
            
        edge_colors.append(color)
        edge_widths.append(1 + 2 * G[u][v]['lanes'])  # Width based on lanes
    
    # Draw road network
    nx.draw_networkx_nodes(G, pos, node_color='lightblue', node_size=300)
    nx.draw_networkx_labels(G, pos)
    nx.draw_networkx_edges(G, pos, edge_color=edge_colors, width=edge_widths, arrowsize=15)
    
    # Draw vehicles on edges (between nodes)
    for vehicle in vehicles:
        if vehicle["current_edge"] and vehicle["progress_on_edge"] > 0:
            start, end = vehicle["current_edge"]
            progress = vehicle["progress_on_edge"]
            
            # Interpolate position along the edge
            start_pos = np.array(pos[start])
            end_pos = np.array(pos[end])
            vehicle_pos = start_pos + progress * (end_pos - start_pos)
            
            plt.plot(vehicle_pos[0], vehicle_pos[1], 'ko', markersize=5)
    
    # Count vehicles per node
    vehicle_counts = {node: 0 for node in G.nodes}
    for vehicle in vehicles:
        if vehicle["current_edge"] is None:  # Only count vehicles at nodes
            vehicle_counts[vehicle["current_position"]] += 1
    
    # Annotate vehicle count
    for node, count in vehicle_counts.items():
        if count > 0:
            plt.text(pos[node][0], pos[node][1] + 0.05, str(count), fontsize=12, ha='center')
    
    # Add legend for congestion levels
    plt.plot([], [], color='green', linewidth=3, label='Low traffic')
    plt.plot([], [], color='yellow', linewidth=3, label='Medium traffic')
    plt.plot([], [], color='red', linewidth=3, label='High traffic')
    plt.legend()
    
    # Add simulation stats if available
    if simulation:
        stats_text = (
            f"Simulation time: {simulation.simulation_time}s\n"
            f"Vehicles in transit: {len([v for v in vehicles if v['current_position'] != v['route'][-1]])}\n"
            f"Avg travel time: {simulation.get_average_travel_time():.1f}s"
        )
        plt.figtext(0.02, 0.02, stats_text, bbox=dict(facecolor='white', alpha=0.5))
    
    plt.title("Traffic Simulation")
    plt.axis('off')
    plt.tight_layout()
    plt.show()

def create_traffic_animation(city_graph, simulation, vehicles, frames=100, interval=100):
    """Create an animation of traffic flow"""
    import numpy as np
    import networkx as nx
    from matplotlib import animation
    
    G = city_graph.get_graph()
    pos = nx.get_node_attributes(G, 'pos')
    
    fig, ax = plt.subplots(figsize=(12, 10))
    
    # Initialize plot elements
    nodes = nx.draw_networkx_nodes(G, pos, node_color='lightblue', node_size=300, ax=ax)
    nx.draw_networkx_labels(G, pos, ax=ax)
    
    # Draw edges - but store the edges differently
    edge_colors = ['green'] * len(G.edges())
    edge_widths = [1 + 2 * G[u][v]['lanes'] for u, v in G.edges()]
    
    # Create the edge collection - store as a global variable for the closure
    edges = nx.draw_networkx_edges(
        G, pos, 
        edge_color=edge_colors, 
        width=edge_widths,
        arrowsize=15,
        ax=ax
    )
    
    # Vehicle scatter plot (initially empty)
    vehicle_scatter = ax.scatter([], [], c='black', s=30)
    
    # Text for stats
    stats_text = ax.text(0.02, 0.02, "", transform=ax.transAxes,
                         bbox=dict(facecolor='white', alpha=0.5))
    
    # Store edge list for updates
    edge_list = list(G.edges())
    
    def update(frame):
        nonlocal edges  # Use the outer scope variable
        
        # Move vehicles
        simulation.move_vehicles()
        
        # Update edge colors based on congestion
        new_edge_colors = []
        for u, v in edge_list:
            flow = G[u][v].get('current_flow', 0)
            capacity = G[u][v].get('capacity', 1)
            ratio = flow / capacity if capacity > 0 else 0
            
            if ratio < 0.5:
                color = 'green'
            elif ratio < 0.8:
                color = 'yellow'
            else:
                color = 'red'
                
            new_edge_colors.append(color)
        
        # Remove old edges and redraw with new colors
        if edges:
            edges.remove()
        edges = nx.draw_networkx_edges(
            G, pos, 
            edge_color=new_edge_colors,
            width=edge_widths,
            arrowsize=15,
            ax=ax
        )
        
        # Update vehicle positions
        vehicle_x = []
        vehicle_y = []
        
        for vehicle in vehicles:
            if vehicle.get("current_edge") and vehicle.get("progress_on_edge", 0) > 0:
                start, end = vehicle["current_edge"]
                progress = vehicle["progress_on_edge"]
                
                # Interpolate position along the edge
                start_pos = np.array(pos[start])
                end_pos = np.array(pos[end])
                vehicle_pos = start_pos + progress * (end_pos - start_pos)
                
                vehicle_x.append(vehicle_pos[0])
                vehicle_y.append(vehicle_pos[1])
        
        # Update vehicle scatter plot
        if vehicle_x and vehicle_y:  # Only update if there are vehicles to show
            vehicle_scatter.set_offsets(np.column_stack([vehicle_x, vehicle_y]))
        
        # Update stats text
        vehicles_in_transit = len([v for v in vehicles 
                               if v.get('current_position') != v.get('route', [])[-1]])
        avg_travel_time = simulation.get_average_travel_time()
        stats = (f"Time: {simulation.simulation_time}s\n"
                f"Vehicles in transit: {vehicles_in_transit}\n"
                f"Avg travel time: {avg_travel_time:.1f}s")
        stats_text.set_text(stats)
        
        # Increment simulation time
        simulation.simulation_time += 1
        
        return [edges, vehicle_scatter, stats_text]
    
    ani = animation.FuncAnimation(fig, update, frames=frames, 
                                 interval=interval, blit=True)
    
    plt.title("Traffic Simulation")
    plt.axis('off')
    plt.tight_layout()
    
    return ani