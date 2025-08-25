from .networkx_graph import CityGraph

def setup_grid_city(rows=3, cols=3, road_length=100, speed_limit=50, lanes=2):
    """Generate a grid-based city layout with dynamic intersection types."""
    city = CityGraph()
    node_positions = {}
    node_id = 1
    for i in range(rows):
        for j in range(cols):
            is_internal = (0 < i < rows - 1) and (0 < j < cols - 1)
            node_type = "traffic_light" if is_internal else "priority"
            
            node_positions[(i, j)] = node_id
            city.add_intersection(node_id, (i * road_length, j * road_length))
            city.graph.nodes[node_id]['type'] = node_type
            node_id += 1

    for (i, j), node_id in node_positions.items():
        if j < cols - 1:
            right_node = node_positions[(i, j + 1)]
            city.add_road(node_id, right_node, length=road_length, speed_limit=speed_limit, lanes=lanes)
            city.add_road(right_node, node_id, length=road_length, speed_limit=speed_limit, lanes=lanes)
        if i < rows - 1:
            down_node = node_positions[(i + 1, j)]
            city.add_road(node_id, down_node, length=road_length, speed_limit=speed_limit, lanes=lanes)
            city.add_road(down_node, node_id, length=road_length, speed_limit=speed_limit, lanes=lanes)
    
    edge_nodes = []
    for (i, j), node_id in node_positions.items():
        if i == 0 or i == rows - 1 or j == 0 or j == cols - 1:
            edge_nodes.append(node_id)
            
    return city, node_positions, edge_nodes

def setup_arterial_road(main_road_length=5, cross_streets=3, road_length=500, speed_limit=70, lanes=3):
    """
    Generates a map with one long main arterial road and several smaller cross-streets.
    """
    city = CityGraph()
    
    main_nodes = []
    for i in range(main_road_length):
        node_id = i + 1
        city.add_intersection(node_id, (i * road_length, 0))
        city.graph.nodes[node_id]['type'] = "traffic_light"
        main_nodes.append(node_id)

    for i in range(len(main_nodes) - 1):
        city.add_road(main_nodes[i], main_nodes[i+1], length=road_length, speed_limit=speed_limit, lanes=lanes)
        city.add_road(main_nodes[i+1], main_nodes[i], length=road_length, speed_limit=speed_limit, lanes=lanes)

    node_id_counter = main_road_length + 1
    edge_nodes = [main_nodes[0], main_nodes[-1]]
    
    arterial_intersections = main_nodes[1:-1]
    for i in range(cross_streets):
        if i < len(arterial_intersections):
            main_intersection = arterial_intersections[i]
            
            north_node = node_id_counter
            south_node = node_id_counter + 1
            city.add_intersection(north_node, (city.graph.nodes[main_intersection]['pos'][0], road_length))
            city.add_intersection(south_node, (city.graph.nodes[main_intersection]['pos'][0], -road_length))
            
            city.add_road(north_node, main_intersection, length=road_length, speed_limit=40, lanes=1)
            city.add_road(main_intersection, north_node, length=road_length, speed_limit=40, lanes=1)
            city.add_road(south_node, main_intersection, length=road_length, speed_limit=40, lanes=1)
            city.add_road(main_intersection, south_node, length=road_length, speed_limit=40, lanes=1)
            
            edge_nodes.extend([north_node, south_node])
            node_id_counter += 2
            
    return city, {}, edge_nodes