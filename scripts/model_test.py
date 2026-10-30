import json

from flowtrace.models import DataFlow

# What a good answer from the model will look like.
good = {
    "source": "orders-service",
    "destination": "payments-service",
    "data": "order id and total amount",
    "mechanism": "http_api",
    "confidence": "high",
    "evidence": [{"file": "app/checkout.py", "start_line": 42,
                  "end_line": 45, "snippet": "requests.post(PAYMENTS_URL, ...)"}],
}

# A bad answer: unknown mechanism and no evidence.
bad = {"source": "orders-service", "destination": "mystery",
       "data": "something", "mechanism": "telepathy", "confidence": "high"}

for name, raw in [("GOOD", good), ("BAD", bad)]:
    flow = DataFlow.from_dict(raw, repo="demo-shop")
    problems = flow.validate()
    print(f"{name}: {'valid' if not problems else problems}")

print("\nAs JSON:")
print(json.dumps(DataFlow.from_dict(good, repo="demo-shop").to_dict(), indent=2))