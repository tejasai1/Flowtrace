from flowtrace.models import DataFlow

REPOS = ["orders-service", "payments-service", "shipping-service"]
ALIASES = {"pg-main": "orders-db"}

SAMPLE = [
    ("orders-service", "orders-service", "PAYMENTS_URL", "order id and total", "http_api",
     "app/checkout.py", 41, 43,
     'resp = requests.post(f"{os.environ[\'PAYMENTS_URL\']}/charge",\n'
     '                     json={"order_id": order.id, "amount": order.total})'),
    ("orders-service", "orders-service", "pg-main", "orders (id, email, total)", "database",
     "app/db.py", 12, 13,
     'conn = psycopg2.connect(host="pg-main", dbname="orders")\n'
     'cur.execute("INSERT INTO orders (id, email, total) VALUES (%s, %s, %s)", row)'),
    ("shipping-service", "shipping-service", "http://payments-service:8000/charge",
     "shipping fee", "http_api", "src/fees.py", 27, 27,
     'requests.post("http://payments-service:8000/charge", json={"fee": fee})'),
    ("payments-service", "payments-service", "https://api.stripe.com/v1",
     "card charges", "external_service", "payments/stripe_client.py", 18, 19,
     'stripe.api_base = "https://api.stripe.com/v1"\n'
     'stripe.Charge.create(amount=amount, currency="usd", source=token)'),
]


def sample_flows():
    flows = []
    for repo, src, dst, data, mech, file, start, end, snippet in SAMPLE:
        flows.append(DataFlow.from_dict({
            "source": src, "destination": dst, "data": data, "mechanism": mech,
            "confidence": "high",
            "evidence": [{"file": file, "start_line": start,
                          "end_line": end, "snippet": snippet}]}, repo))
    return flows