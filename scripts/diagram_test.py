from flowtrace.diagram import write_html
from flowtrace.graph import build_graph
from scripts.sample_data import ALIASES, REPOS, sample_flows

graph = build_graph(sample_flows(), REPOS, ALIASES)
path = write_html(graph, "output/diagram.html", "Demo company: data flow map")
print(f"Diagram written to {path.resolve()}")