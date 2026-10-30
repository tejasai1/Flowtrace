from flowtrace.pipeline import run
from flowtrace.providers import get_provider

provider = get_provider()  # the real Muse Spark, as set in config.yaml
print(f"Analyzing with {provider.model} ...\n")

graph, report = run("..", provider, output_dir="output/real_run")

print("\nSystems found:")
for n in graph["nodes"]:
    print(f"  {n['label']}")

print("\nData flows found:")
labels = {n["id"]: n["label"] for n in graph["nodes"]}
for e in graph["edges"]:
    print(f"  {labels[e['source']]} -> {labels[e['destination']]} "
          f"[{e['mechanism']}] {e['data']}")

for repo, info in report.items():
    for item in info["rejected"]:
        print(f"\nREJECTED in {repo}: {item['flow'].get('destination')} "
              f"-> {item['problems']}")