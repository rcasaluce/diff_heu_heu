import argparse
import os
import sys
import pandas as pd
import numpy as np
import pm4py
import graphviz
import pydotplus
import pygraphviz as pgv

from pm4py.objects.conversion.log import converter as log_converter
from pm4py.objects.log.importer.xes import importer as xes_importer
from pm4py.objects.log.util import dataframe_utils
from pm4py.algo.discovery.heuristics import algorithm as heuristics_miner
from pm4py.visualization.heuristics_net import visualizer as hn_visualizer
from pm4py.objects.conversion.process_tree import converter as pt_converter
from pm4py.algo.filtering.log.end_activities import end_activities_filter

def pre_processing_logs(file_path):
    """
    Pre-processes the event log CSV file.
    
    Steps:
    1. Load the event log from CSV.
    2. Convert 'AttackAttempts' to int64 if it exists.
    3. If 'state' exists:
        a. Remove rows where 'state' is 'Complete' and 'activity' is 'deadlock'.
        b. Combine 'state' and 'activity' into a single 'activity' column.
    4. Ensure 'caseID' is of type string.
    5. Create timestamp and date columns.
    6. Format the DataFrame for pm4py.
    
    Args:
        file_path (str): Path to the CSV file.
        
    Returns:
        pm4py.util.importer.DataFrame: Formatted event log.
    """
    # Load the event log from the CSV file
    event_log = pd.read_csv(file_path, sep=',')

    # 1. Convert 'AttackAttempts' to int64 if it exists
    if 'AttackAttempts' in event_log.columns:
        event_log['AttackAttempts'] = event_log['AttackAttempts'].astype(np.int64)

    # 2. Remove rows where 'activity' is 'noMoreStepsNecessary'
    if 'activity' in event_log.columns:
        # Check if 'state' exists before accessing it
        if 'state' in event_log.columns:
            complete_not_in_state = 'Complete' not in event_log['state'].values
        else:
            complete_not_in_state = True  # Since 'state' doesn't exist

        if complete_not_in_state:
            event_log = event_log.drop(event_log[event_log['activity'] == 'noMoreStepsNecessary'].index)

    # 3. Conditional operations based on the existence of the 'state' column
    if 'state' in event_log.columns:
        # a. Remove rows where 'state' is 'Complete' and 'activity' is 'deadlock'
        condition = (event_log['state'] == 'Complete') & (event_log['activity'] == 'deadlock')
        event_log = event_log.drop(event_log[condition].index)

        # b. Combine 'state' and 'activity' into a single 'activity' column
        event_log['activity'] = event_log.apply(
            lambda row: '-'.join([row['state'], row['activity']]),
            axis=1
        )

        # c. Remove entire cases that end with 'noMoreStepsNecessary'
        last_events = event_log.groupby('caseID').tail(1).reset_index(drop=True)
        cases_to_remove = last_events[last_events['activity'].str.contains('noMoreStepsNecessary')]['caseID'].tolist()
        event_log = event_log[~event_log['caseID'].isin(cases_to_remove)]

    # 4. Ensure 'caseID' is of type string
    if 'caseID' in event_log.columns:
        event_log['caseID'] = event_log['caseID'].astype(str)

    # 5. Create timestamp and date columns
    if 'time' in event_log.columns:
        # Note: The original logic adds an offset to 'time'
        event_log['timestamp'] = event_log['time'] + 1617295944.17324
        event_log['date'] = pd.to_datetime(event_log['timestamp'], unit='s', origin='unix')
    else:
        raise KeyError("The 'time' column does not exist in the event log.")

    # 6. Format the DataFrame for pm4py
    required_cols = ['caseID', 'activity', 'date']
    if all(col in event_log.columns for col in required_cols):
        event_log_plus_modes_activity = pm4py.format_dataframe(
            event_log,
            case_id='caseID',
            activity_key='activity',
            timestamp_key='date',
            timest_format='%Y-%m-%d %H:%M:%S%z'
        )
    else:
        missing_cols = [col for col in required_cols if col not in event_log.columns]
        raise KeyError(f"The following columns are missing in the event log: {missing_cols}")

    # 7. Obtain start and end activities (optional)
    pm4py.get_start_activities(event_log_plus_modes_activity)
    pm4py.get_end_activities(event_log_plus_modes_activity)

    # Return the formatted DataFrame
    return event_log_plus_modes_activity



def heu(event_log):
    """
    Applies the Heuristics Miner algorithm to the event log.
    
    Args:
        event_log (pm4py.util.importer.DataFrame): Formatted event log.
        
    Returns:
        pm4py.objects.heuristics_net.obj.HeuristicsNet: Heuristics network.
    """
    # Apply Heuristics Miner
    heu_net = heuristics_miner.apply_heu(event_log, parameters={"dfg_pre_cleaning_noise_thresh": 0})

    # Visualization (optional)
    hn_visualizer.apply(heu_net)

    return heu_net

def crea_text_dot(heu_net):
    """
    Transforms the heuristics network into a DOT file string.
    
    Args:
        heu_net (pm4py.objects.heuristics_net.obj.HeuristicsNet): Heuristics network.
        
    Returns:
        str: DOT file string.
    """
    # Transform heu_net into DOT file
    dot_file = hn_visualizer.get_graph(heu_net)
    output_graphviz_dot = dot_file.create_dot()
    graph = pydotplus.graph_from_dot_data(output_graphviz_dot)
    data = graph.to_string()

    return data

def parse_dot_string(data):
    """
    Parses the DOT string and returns graph components.
    
    Args:
        data (str): DOT file string.
        
    Returns:
        tuple: Contains edges, labels, binary node names, edge labels, and node positions.
    """
    graph = pgv.AGraph(data)
    edges_origin_dest = []
    list_edges_labels = []
    for e in graph.edges():
        edges_origin_dest.append(e)
        list_edges_labels.append((e[0], e[1], e.attr.get('label', '')))

    labels = []
    for node in graph.nodes():
        if 'label' in node.attr:
            labels.append(node.attr['label'])
    if '\\N' in labels:
        labels.remove('\\N')

    binary_names = []
    dict_node_pos = {}
    for node in graph.nodes():
        binary_names.append(node)
        if node != '\\n':
            dict_node_pos[node] = node.attr.get('pos', '')

    return edges_origin_dest, labels, binary_names, list_edges_labels, dict_node_pos

def match_binary_names_labels(edges_origin_dest, binary_names, labels):
    """
    Matches binary node names with their original names.
    
    Args:
        edges_origin_dest (list): List of edge objects.
        binary_names (list): List of binary node names.
        labels (list): List of labels parsed from the DOT file.
        
    Returns:
        list: List of matched edges with original names.
    """
    labels_names_inv = dict(zip(binary_names, [label.split(' ')[0] for label in labels]))
    edges_origin_dest_labels = []
    for edge in edges_origin_dest:
        origin = labels_names_inv.get(edge[0], edge[0])
        destination = labels_names_inv.get(edge[1], edge[1])
        edges_origin_dest_labels.append((origin, destination))
    return edges_origin_dest_labels

def unique_el(edges_origin_dest_labels):
    """
    Flattens the list of tuples and removes duplicates.
    
    Args:
        edges_origin_dest_labels (list): List of edge tuples.
        
    Returns:
        list: List of unique elements.
    """
    flattened_data = [item for sublist in edges_origin_dest_labels for item in sublist]
    unique_elements = list(set(flattened_data))
    return unique_elements

def create_dict_diff(list1, list2):
    """
    Creates a dictionary showing differences between two lists.
    
    Args:
        list1 (list): First list.
        list2 (list): Second list.
        
    Returns:
        dict: Dictionary with 'green' and 'red' keys indicating differences.
    """
    red_values = set(list1) - set(list2)  # New elements
    green_values = set(list2) - set(list1)  # Removed elements
    dict_diff = {'green': list(green_values), 'red': list(red_values)}
    return dict_diff

def create_dict_diff_edges(list1, list2):
    """
    Creates a dictionary showing differences between two edge lists.
    
    Args:
        list1 (list): First list of edges.
        list2 (list): Second list of edges.
        
    Returns:
        dict: Dictionary with 'green' and 'red' keys indicating edge differences.
    """
    set1 = set(map(tuple, list1))
    set2 = set(map(tuple, list2))
    red_values = set1 - set2
    green_values = set2 - set1
    dict_diff_edges = {'green': list(green_values), 'red': list(red_values)}
    return dict_diff_edges

def from_list_edges_to_dict(edges_origin_dest_labels):
    """
    Converts a list of edge tuples to a dictionary.
    
    Args:
        edges_origin_dest_labels (list): List of edge tuples.
        
    Returns:
        dict: Dictionary mapping edge tuples to '-'.
    """
    list_activity_labels = {}
    for edge in edges_origin_dest_labels:
        list_activity_labels[(edge[0].split(' ')[0], edge[1].split(' ')[0])] = '-'
    return list_activity_labels

def diff(dfg_old, dfg_new):
    """
    Compares two Directly-Follows Graph (DFG) dictionaries and returns the differences.
    
    Args:
        dfg_old (dict): Old DFG dictionary.
        dfg_new (dict): New DFG dictionary.
        
    Returns:
        tuple: Two dictionaries representing the differences and the new differences.
    """
    dfg_result = {}
    dfg_result_new = {}

    for edge in dfg_old:
        if edge in dfg_new:
            dfg_result[edge] = 'ok'
            if dfg_old[edge] != '-':
                count = round(float(dfg_old[edge]) - float(dfg_new[edge]), 3)
                dfg_result_new[edge] = count
        else:
            dfg_result[edge] = 'missing'
            dfg_result_new[edge] = ''

    for edge in dfg_new:
        if edge not in dfg_old:
            dfg_result[edge] = 'extra'

    return dfg_result, dfg_result_new

def modifica_dfg_result(dfg_result):
    """
    Modifies the keys of the dictionary by replacing '@@S' with 'Start' and '@@E' with 'End'.
    
    Args:
        dfg_result (dict): Original dictionary with tuple keys.
        
    Returns:
        dict: Modified dictionary with updated keys.
    """
    return {
        tuple(
            'Start' if item == '@@S' else 'End' if item == '@@E' else item
            for item in key
        ): value
        for key, value in dfg_result.items()
    }

def draw_diff(dfg_diff, dict_diff_nodes, name):
    """
    Draws the difference graph using Graphviz.
    
    Args:
        dfg_diff (dict): Difference dictionary.
        dict_diff_nodes (dict): Dictionary indicating node differences.
        name (str): Output file name (without extension).
        
    Returns:
        graphviz.Digraph: The generated graph.
    """
    dot = graphviz.Digraph(name)

    #dot.graph_attr['rankdir'] = 'LR'  # Left to Right

    unique_keys = set()
    for key in dfg_diff.keys():
        unique_keys.update(key)

    common_node_attributes = {
        'fillcolor': "#33CBCB",
        'fontcolor': 'black',
        'shape': 'box',
        'style': 'filled',
        'width': '1.4514',
        'height': '0.5'
    }

    for a in unique_keys:
        node_attributes = common_node_attributes.copy()

        if a == 'Start':
            node_attributes['fillcolor'] = "#32CD32"
            node_attributes['shape'] = 'circle'
            node_attributes['width'] = "0.75"
            node_attributes['label'] = ""
        elif a == 'End':
            node_attributes['fillcolor'] = "#FFA500"
            node_attributes['shape'] = 'circle'
            node_attributes['width'] = "0.75"
            node_attributes['label'] = ""
            node_attributes['color'] = '#FFFFFF'
        elif a in dict_diff_nodes['green']:
            node_attributes['fillcolor'] = 'white'
            node_attributes['color'] = '#0d79ec'
            node_attributes['penwidth'] = '2'
        elif a in dict_diff_nodes['red']:
            node_attributes['fillcolor'] = 'white'
            node_attributes['color'] = '#ec555b'
            node_attributes['penwidth'] = '2'
        else:
            node_attributes['fillcolor'] = 'white'

        dot.node(a, **node_attributes)

    for key in dfg_diff:
        if key[0] in dict_diff_nodes['green'] or key[1] in dict_diff_nodes['green']:
            color = '#0d79ec'
            style = 'solid'
        else:
            color = 'black' if dfg_diff[key] == 'ok' else 'red'
            style = 'solid'
        dot.edge(key[0], key[1], color=color, style=style, label="")

    dot.graph_attr['ratio'] = 'auto'
    dot.graph_attr['size'] = '100,100'

    if len(dfg_diff) == 0:
        dot.node('There are no differences between the formal model and the simulated one!', color='white')

    dot.render(filename=name, format='pdf', cleanup=True)  # Save as PDF
    print(f"Graph saved as {name}.pdf")
    return dot

def imp_edges_modified(diff_dict):
    """
    Filters the differences by removing edges marked as 'ok'.
    
    Args:
        diff_dict (dict): Dictionary with all edges and their statuses.
        
    Returns:
        dict: Filtered dictionary with only important edges.
    """
    new_dfg_diff = {}
    for key, v in diff_dict.items():
        if v != 'ok':
            new_dfg_diff[key] = v
    return new_dfg_diff

def main(args):
    """
    Main function to process logs, apply Heuristics Miner, and generate difference visualizations.
    
    Args:
        args (argparse.Namespace): Parsed command-line arguments.
    """
    # Pre-processing the logs
    print("Pre-processing the logs...")
    event_log_old = pre_processing_logs(args.file_path_old)
    event_log_new = pre_processing_logs(args.file_path_new)

    # Applying Heuristics Miner
    print("Applying Heuristics Miner...")
    heu_net_old = heu(event_log_old)
    heu_net_new = heu(event_log_new)

    # Creating DOT strings
    print("Creating DOT strings...")
    data_old = crea_text_dot(heu_net_old)
    data_new = crea_text_dot(heu_net_new)

    # Parsing DOT strings
    print("Parsing DOT strings...")
    edges_origin_dest_old, labels_old, binary_names_old, list_edges_labels_old, dict_node_pos_old = parse_dot_string(data_old)
    edges_origin_dest_new, labels_new, binary_names_new, list_edges_labels_new, dict_node_pos_new = parse_dot_string(data_new)

    # Matching binary names to original names
    print("Matching binary names to original names...")
    edges_origin_dest_labels_new = match_binary_names_labels(edges_origin_dest_new, binary_names_new, labels_new)
    edges_origin_dest_labels_old = match_binary_names_labels(edges_origin_dest_old, binary_names_old, labels_old)

    # Identifying unique elements
    print("Identifying unique elements...")
    unique_elements_old = unique_el(edges_origin_dest_labels_old)
    unique_elements_new = unique_el(edges_origin_dest_labels_new)

    # Creating difference dictionaries
    print("Creating difference dictionaries...")
    dict_diff_nodes = create_dict_diff(unique_elements_old, unique_elements_new)
    dict_diff_edges = create_dict_diff_edges(edges_origin_dest_labels_old, edges_origin_dest_labels_new)

    # Converting edge lists to dictionaries
    print("Converting edge lists to dictionaries...")
    list_activity_labels_new = from_list_edges_to_dict(edges_origin_dest_labels_new)
    list_activity_labels_old = from_list_edges_to_dict(edges_origin_dest_labels_old)

    # Calculating differences between DFGs
    print("Calculating differences between DFGs...")
    dfg_result, dfg_result_new = diff(list_activity_labels_old, list_activity_labels_new)

    # Modifying DFG results
    print("Modifying DFG results...")
    dfg_result_modified = modifica_dfg_result(dfg_result)

    # Drawing differences
    print("Drawing differences...")
    draw_diff(dfg_result_modified, dict_diff_nodes, args.output_full)

    # Filtering differences
    print("Filtering differences...")
    dfg_result_modified_filtered = imp_edges_modified(dfg_result_modified)
    draw_diff(dfg_result_modified_filtered, dict_diff_nodes, args.output_filtered_full)

    print("Process completed.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process event logs and generate difference visualizations.")

    parser.add_argument('--file_path_old', type=str, required=True, help='Path to RobBank_initial_set_experiment.csv')
    parser.add_argument('--file_path_new', type=str, required=True, help='Path to RobBank_final_set_experiment.csv')
    parser.add_argument('--output_full', type=str, default='prova_heu_heu_robbank_full', help='Filename for complete differences PDF')
    parser.add_argument('--output_filtered_full', type=str, default='prova_heu_heu_robbank_filtered_full', help='Filename for filtered complete differences PDF')

    args = parser.parse_args()

    # Verify that input files exist
    for file_arg in ['file_path_old', 'file_path_new']:
        file_path = getattr(args, file_arg)
        if not os.path.isfile(file_path):
            print(f"Error: The file {file_path} specified for {file_arg} does not exist.")
            sys.exit(1)

    main(args)
