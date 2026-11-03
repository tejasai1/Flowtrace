import json
from pathlib import Path

from flowtrace.diagram import write_html
from flowtrace.impact import assess_all
from flowtrace.providers import get_provider

SOURCE = "output/robot_shop_vulns/graph.json"   # data flows + vulnerabilities
OUTPUT = "output/robot_shop_impact"

with open(SOURCE, encoding="utf-8") as f:
    graph = json.load(f)

provider = get_provider()
print(f"Assessing impact with {provider.model} ...\n")
assess_all(provider, graph)

Path(OUTPUT).mkdir(parents=True, exist_ok=True)
Path(f"{OUTPUT}/graph.json").write_text(json.dumps(graph, indent=2), encoding="utf-8")
path = write_html(graph, f"{OUTPUT}/diagram.html",
                  "Robot Shop: data flows, vulnerabilities and impact")

order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
ranked = sorted((n for n in graph["nodes"] if n.get("impact")),
                key=lambda n: order.get(n["impact"].get("risk_level"), 9))
print("\nRisk ranking:")
for n in ranked:
    print(f"  {n['impact'].get('risk_level', '?'):9} {n['label']}: {n['impact'].get('summary', '')}")
print(f"\nDiagram written to {path.resolve()}")