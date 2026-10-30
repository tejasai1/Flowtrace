import json

from flowtrace.diagram import write_html
from flowtrace.graph import build_graph, normalize_name
from flowtrace.models import DataFlow

SERVICES = ["cart", "catalogue", "dispatch", "payment",
            "ratings", "shipping", "user", "web"]

with open("output/robot_shop/flows.json", encoding="utf-8") as f:
    raw = json.load(f)
flows = [DataFlow.from_dict(d, d["repo"]) for d in raw]
print(f"Loaded {len(flows)} saved flows")

print("\nURL name fix:", normalize_name("payment gateway (https://paypal.com/)"))

graph = build_graph(flows, SERVICES)
labels = {n["id"]: n["label"] for n in graph["nodes"]}

print(f"\nSystems ({len(graph['nodes'])}):")
for n in graph["nodes"]:
    print(f"  {n['label']}")

print(f"\nData flows ({len(graph['edges'])}):")
for e in graph["edges"]:
    print(f"  {labels[e['source']]} -> {labels[e['destination']]} "
          f"[{e['mechanism']}] evidence: {len(e['evidence'])}")

path = write_html(graph, "output/robot_shop_rebuilt/diagram.html",
                  "Robot Shop data flow map (rebuilt)")
print(f"\nDiagram written to {path.resolve()}")