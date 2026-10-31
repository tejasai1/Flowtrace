import os

from flowtrace.pipeline import run
from flowtrace.providers import get_provider

# Stan's Robot Shop by Instana (Apache License 2.0)
# https://github.com/instana/robot-shop, commit 55292e2199f2fb00a165b1f7d3045fe7f8922038
WORKSPACE = os.path.expanduser("~/flowtrace-demos/robot-shop")
SERVICES = ["cart", "catalogue", "dispatch", "payment",
            "ratings", "shipping", "user", "web"]
OUTPUT = "output/robot_shop_v3"

provider = get_provider()
print(f"Analyzing {len(SERVICES)} Robot Shop services with {provider.model} ...\n")
graph, report = run(WORKSPACE, provider, output_dir=OUTPUT, only=SERVICES)

labels = {n["id"]: n["label"] for n in graph["nodes"]}
print(f"\nSystems found ({len(graph['nodes'])}):")
for n in graph["nodes"]:
    print(f"  {n['label']:22} {'[service]' if n['is_repo'] else '[external]'}")

sensitive = [e for e in graph["edges"] if e["sensitive"]]
print(f"\nData flows found ({len(graph['edges'])}, {len(sensitive)} sensitive):")
for e in graph["edges"]:
    mark = "!!" if e["sensitive"] else "  "
    print(f" {mark} {labels[e['source']]} -> {labels[e['destination']]} "
          f"[{e['category'] or '?'}] {'; '.join(e['data'])}")

for repo, info in report.items():
    for item in info["rejected"]:
        print(f"\nREJECTED in {repo}: {item['flow'].get('source')} -> "
              f"{item['flow'].get('destination')}: {item['problems']}")