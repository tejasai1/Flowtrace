from flowtrace.graph import build_graph, normalize_name
from flowtrace.models import DataFlow


def flow(repo, source, destination, data, mechanism):
    ev = [{"file": "app.py", "start_line": 1, "end_line": 1, "snippet": ""}]
    return DataFlow.from_dict({"source": source, "destination": destination,
                               "data": data, "mechanism": mechanism,
                               "confidence": "high", "evidence": ev}, repo)


print("Name cleanup:")
for name in ["PAYMENTS_URL", "http://payments-service:8000/charge",
             "payments-service", "ORDERS_DB_HOST"]:
    print(f"  {name:40} -> {normalize_name(name)}")

flows = [
    flow("orders-service", "orders-service", "PAYMENTS_URL", "order total", "http_api"),
    flow("orders-service", "orders-service", "pg-main", "orders", "database"),
    flow("shipping-service", "shipping-service",
         "http://payments-service:8000/charge", "shipping fee", "http_api"),
    flow("payments-service", "payments-service", "https://api.stripe.com/v1",
         "card charges", "external_service"),
]
repos = ["orders-service", "payments-service", "shipping-service"]
graph = build_graph(flows, repos, aliases={"pg-main": "orders-db"})

print(f"\nSystems ({len(graph['nodes'])}):")
for n in graph["nodes"]:
    kind = "repo" if n["is_repo"] else "external"
    print(f"  {n['label']:20} [{kind}]  seen as: {n['names_seen']}")

print(f"\nData flows ({len(graph['edges'])}):")
for e in graph["edges"]:
    print(f"  {e['source']} -> {e['destination']} [{e['mechanism']}] {e['data']}")