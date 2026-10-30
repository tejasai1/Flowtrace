import json

from flowtrace.extractor import build_messages, parse_response
from flowtrace.reader import read_repository

files = read_repository(".")
messages = build_messages("flowtrace", files)
print(f"Prompt: {len(messages)} messages, {len(files)} files, "
      f"{len(messages[1]['content'])} characters")
print("\nStart of what the model will see:\n")
print(messages[1]["content"][:400])

# A pretend model reply: one real flow and two invented ones.
fake_reply = json.dumps({"flows": [
    {"source": "flowtrace", "destination": "Meta Model API",
     "data": "prompts and repository code", "mechanism": "external_service",
     "confidence": "high",
     "evidence": [{"file": "flowtrace/providers/openai_compatible.py",
                   "start_line": 20, "end_line": 24, "snippet": "(model's version)"}]},
    {"source": "flowtrace", "destination": "billing-db", "data": "invoices",
     "mechanism": "database", "confidence": "high",
     "evidence": [{"file": "app/billing.py", "start_line": 1, "end_line": 2, "snippet": "..."}]},
    {"source": "flowtrace", "destination": "audit-log", "data": "events",
     "mechanism": "file", "confidence": "low",
     "evidence": [{"file": "config.yaml", "start_line": 500, "end_line": 505, "snippet": "..."}]},
]})

accepted, rejected = parse_response(fake_reply, "flowtrace", files)

print(f"\nACCEPTED ({len(accepted)}):")
for flow in accepted:
    print(f"  {flow.source} -> {flow.destination} [{flow.mechanism}]")
    print("  Real code from the evidence lines:")
    print("    " + flow.evidence[0].snippet.replace("\n", "\n    "))

print(f"\nREJECTED ({len(rejected)}):")
for raw, problems in rejected:
    print(f"  {raw['source']} -> {raw['destination']}: {problems}")