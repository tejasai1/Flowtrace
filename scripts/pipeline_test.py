from flowtrace.pipeline import run
from flowtrace.providers.fake import FakeProvider

# What we expect Muse Spark to answer for the flowtrace repository:
# one real flow, and one invented flow that must be rejected.
reply = {"flows": [
    {"source": "flowtrace", "destination": "Meta Model API",
     "data": "prompts and repository code", "mechanism": "external_service",
     "confidence": "high",
     "category": "business",
     "evidence": [{"file": "flowtrace/providers/openai_compatible.py",
                   "start_line": 20, "end_line": 24, "snippet": ""}]},
    {"source": "flowtrace", "destination": "secret-db", "data": "everything",
     "mechanism": "database", "confidence": "high",
     "category": "business",
     "evidence": [{"file": "db/secret.py", "start_line": 1, "end_line": 5, "snippet": ""}]},
]}

provider = FakeProvider({"flowtrace": reply})

# ".." is your FlowtraceAI folder, which contains the flowtrace repository.
graph, report = run("..", provider, output_dir="output/pipeline_test")

print(f"\nSystems: {[n['label'] for n in graph['nodes']]}")
print(f"Model calls: {provider.calls}")
print(f"Rejected: {report['flowtrace']['rejected'][0]['problems']}")