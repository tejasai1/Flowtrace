import os

from flowtrace.pipeline import run
from flowtrace.providers import get_provider

# Stan's Robot Shop by Instana (Apache License 2.0)
# https://github.com/instana/robot-shop, commit 55292e2199f2fb00a165b1f7d3045fe7f8922038
WORKSPACE = os.path.expanduser("~/flowtrace-demos/robot-shop")
SERVICES = ["cart", "catalogue", "dispatch", "payment",
            "ratings", "shipping", "user", "web"]

provider = get_provider()
print(f"Analyzing {len(SERVICES)} Robot Shop services with {provider.model} ...\n")
graph, report = run(WORKSPACE, provider, output_dir="output/robot_shop", only=SERVICES)

labels = {n["id"]: n["label"] for n in graph["nodes"]}
print(f"\nSystems found ({len(graph['nodes'])}):")
for n in graph["nodes"]:
    print(f"  {n['label']:20} {'[service]' if n['is_repo'] else '[external]'}")

print(f"\nData flows found ({len(graph['edges'])}):")
for e in graph["edges"]:
    print(f"  {labels[e['source']]} -> {labels[e['destination']]} [{e['mechanism']}]")

for repo, info in report.items():
    for item in info["rejected"]:
        print(f"\nREJECTED in {repo}: {item['flow'].get('source')} -> "
              f"{item['flow'].get('destination')}: {item['problems']}")