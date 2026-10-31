import json
import sys

from flowtrace.diagram import write_html

folder = sys.argv[1] if len(sys.argv) > 1 else "output/robot_shop_v2"
with open(f"{folder}/graph.json", encoding="utf-8") as f:
    graph = json.load(f)

path = write_html(graph, f"{folder}/diagram.html", "Robot Shop data flow map")
print(f"Redrew {len(graph['nodes'])} systems and {len(graph['edges'])} flows: {path.resolve()}")