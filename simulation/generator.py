import xml.etree.ElementTree as ET
from xml.dom import minidom
import random
import os

def _prettify(elem):
    """Return a pretty-printed XML string for the Element."""
    rough_string = ET.tostring(elem, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="    ")

def generate_node_file(file_name, city_graph):
    """Generates the SUMO .nod.xml file."""
    nodes = ET.Element('nodes')
    for node_id, data in city_graph.nodes(data=True):
        node_type = "traffic_light" if node_id in [6, 7, 10, 11] else "priority"
        ET.SubElement(nodes, 'node', id=str(node_id), x=str(data['pos'][0]), y=str(data['pos'][1]), type=node_type)
    
    with open(file_name, "w") as f:
        f.write(_prettify(nodes))
    print(f"Generated node file: {file_name}")

def generate_edge_file(file_name, city_graph):
    """Generates the SUMO .edg.xml file."""
    edges = ET.Element('edges')
    for u, v, data in city_graph.edges(data=True):
        edge_id = f"edge_{u}-{v}"
        ET.SubElement(edges, 'edge', id=edge_id, attrib={'from': str(u), 'to': str(v), 'numLanes': str(data['lanes'])})

    with open(file_name, "w") as f:
        f.write(_prettify(edges))
    print(f"Generated edge file: {file_name}")

def generate_route_file(file_name, edge_nodes, simulation_time, arrival_rate, scale=1.0):
    """Generates the SUMO .rou.xml file using traffic flows."""
    routes = ET.Element('routes')
    ET.SubElement(routes, 'vType', id="car", accel="2.6", decel="4.5", sigma="0.5", length="5", maxSpeed="70")

    if len(edge_nodes) < 2:
        print("Warning: Not enough edge nodes to generate traffic flow.")
        return

    # Create flows between random pairs of edge nodes
    num_flows = 10  # Define a fixed number of major traffic flows
    for i in range(num_flows):
        origin_node, dest_node = random.sample(edge_nodes, 2)
        flow_id = f"flow_{i}"

        scaled_vehs_per_hour = arrival_rate * 60 / num_flows * scale
        
        # Define the flow
        ET.SubElement(routes, 'flow', id=flow_id, type="car", begin="0", end=str(simulation_time), 
                      vehsPerHour=str(scaled_vehs_per_hour),
                      fromJunction=str(origin_node), toJunction=str(dest_node))

    with open(file_name, "w") as f:
        f.write(_prettify(routes))
    print(f"Generated route file: {file_name}")


def generate_sumo_config(file_name, network_file, route_file, additional_files=None):
    """Generates the main SUMO .sumocfg file."""
    configuration = ET.Element('configuration')
    input_tag = ET.SubElement(configuration, 'input')
    ET.SubElement(input_tag, 'net-file', value=os.path.basename(network_file))
    ET.SubElement(input_tag, 'route-files', value=os.path.basename(route_file))
    
    if additional_files:
        ET.SubElement(input_tag, 'additional-files', value=",".join([os.path.basename(f) for f in additional_files]))

    time_tag = ET.SubElement(configuration, 'time')
    ET.SubElement(time_tag, 'begin', value="0")

    with open(file_name, "w") as f:
        f.write(_prettify(configuration))

def generate_tls_file(file_name, tls_intersections, chromosome, yellow_duration, all_red_duration):
    """
    Generates the SUMO .add.xml file for traffic light logic.
    Assumes a simple 2-phase (NS/EW) light cycle for each intersection.
    """
    additional = ET.Element('additional')
    
    chromo_idx = 0
    for tls_id in tls_intersections:
        ns_green_duration = chromosome[chromo_idx]
        ew_green_duration = chromosome[chromo_idx + 1]
        
        tl_logic = ET.SubElement(additional, 'tlLogic', id=str(tls_id), type="static", programID="1", offset="0")
        
        # Phase 1: North-South Green
        ET.SubElement(tl_logic, 'phase', duration=str(ns_green_duration), state="GGGrrrrrrrGGGrrrrrrr")
        # Phase 2: North-South Yellow
        ET.SubElement(tl_logic, 'phase', duration=str(yellow_duration), state="yyyrrrrrrryyyrrrrrrr")
        # Phase 3: All Red Clearance
        ET.SubElement(tl_logic, 'phase', duration=str(all_red_duration), state="rrrrrrrrrrrrrrrrrrrr")
        # Phase 4: East-West Green
        ET.SubElement(tl_logic, 'phase', duration=str(ew_green_duration), state="rrrrrGGGrrrrrrGGGrrr")
        # Phase 5: East-West Yellow
        ET.SubElement(tl_logic, 'phase', duration=str(yellow_duration), state="rrrrryyyrrrrrryyyrrr")
        # Phase 6: All Red Clearance
        ET.SubElement(tl_logic, 'phase', duration=str(all_red_duration), state="rrrrrrrrrrrrrrrrrrrr")
        
        chromo_idx += 2

    with open(file_name, "w") as f:
        f.write(_prettify(additional))