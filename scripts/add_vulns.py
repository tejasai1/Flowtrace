import json
from pathlib import Path

from flowtrace.diagram import write_html
from flowtrace.vulns import attach_vulnerabilities

SOURCE = "output/robot_shop_v3/graph.json"   # data flows from the v3 run
OUTPUT = "output/robot_shop_vulns"
SERVICES = ["cart", "catalogue", "dispatch", "payment",
            "ratings", "shipping", "user", "web"]
# Robot Shop's published images, as used in its docker-compose.yaml (tag 2.1.0)
IMAGES = {s: f"robotshop/rs-{s}:2.1.0" for s in SERVICES}

with open(SOURCE, encoding="utf-8") as f:
    graph = json.load(f)

attach_vulnerabilities(graph, IMAGES)

Path(OUTPUT).mkdir(parents=True, exist_ok=True)
Path(f"{OUTPUT}/graph.json").write_text(json.dumps(graph, indent=2), encoding="utf-8")
path = write_html(graph, f"{OUTPUT}/diagram.html", "Robot Shop: data flows and vulnerabilities")
print(f"\nDiagram written to {path.resolve()}")