import networkx as nx
import json

graph = nx.read_graphml('lightrag_workspace/graph_chunk_entity_relation.graphml')
types = set([data.get('entity_type', 'UNKNOWN') for node, data in graph.nodes(data=True)])
print('Entity Types in Graph:', types)

sample_nodes = []
for node, data in graph.nodes(data=True):
    if len(sample_nodes) < 5:
        sample_nodes.append((node, data))

print('\nSample Nodes:', json.dumps(sample_nodes, indent=2))
