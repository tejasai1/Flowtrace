import json
import re

RISK_LEVELS = ("critical", "high", "medium", "low")
VULN_ID = re.compile(r"\b(CVE-\d{4}-\d+|GHSA-[0-9a-z]{4}-[0-9a-z]{4}-[0-9a-z]{4})\b", re.IGNORECASE)

SYSTEM_PROMPT = """You are FlowTrace's security analyst. You receive FACTS about one service:
its known vulnerabilities (from a Grype scan of its container image) and the data flows
that pass through it (from code analysis). Explain what is at risk if this service is compromised.

Rules:
- Use ONLY the facts given. Never invent vulnerabilities, systems or data.
- Mention a vulnerability ID only if it appears in the facts.
- Focus on sensitive data (categories personal, payment, credentials) and on which other
  systems an attacker could reach through this service's data flows.
- Prefer fixes in the service's own libraries (app_level: true); those are the easiest to upgrade.
- Write short, plain English for a security reviewer.

Respond with JSON only, in exactly this shape:
{"risk_level": "critical|high|medium|low",
 "summary": "2-3 sentences",
 "data_at_risk": ["..."],
 "exposed_systems": ["system names taken from the facts"],
 "recommendations": ["up to 3 concrete actions"]}"""


def service_facts(graph, node):
    """Collect the facts Muse Spark may use: the scan summary and the service's data flows."""
    labels = {n["id"]: n["label"] for n in graph["nodes"]}
    flows = [{"from": labels[e["source"]], "to": labels[e["destination"]],
              "data": "; ".join(e["data"]), "sends": e.get("fields", []),
              "returns": e.get("returns", []), "category": e["category"],
              "sensitive": e["sensitive"]}
             for e in graph["edges"] if node["id"] in (e["source"], e["destination"])]
    v = node["vulns"]
    return {"service": node["label"],
            "vulnerabilities": {"total": v["unique_vulnerabilities"],
                                "in_own_libraries": v["app_level"],
                                "by_severity": v["by_severity"],
                                "most_serious": v["top"]},
            "data_flows": flows}


def verify(report, facts):
    """Check the assessment only uses facts it was given."""
    problems = []
    if report.get("risk_level") not in RISK_LEVELS:
        problems.append(f"unknown risk level: {report.get('risk_level')}")
    known = {facts["service"].lower()}
    for f in facts["data_flows"]:
        known |= {f["from"].lower(), f["to"].lower()}
    unknown = [s for s in report.get("exposed_systems", []) if str(s).lower() not in known]
    if unknown:
        problems.append(f"systems not in its data flows: {unknown}")
    known_ids = {t["id"].upper() for t in facts["vulnerabilities"]["most_serious"]}
    mentioned = {m.upper() for m in VULN_ID.findall(json.dumps(report))}
    invented = sorted(mentioned - known_ids)
    if invented:
        problems.append(f"vulnerability IDs not in the scan: {invented}")
    return problems


def _load_json(text):
    text = text.strip()
    if text.startswith("```"):  # remove ```json fences if the model adds them
        text = text.strip("`").removeprefix("json").strip()
    return json.loads(text)


def assess_service(provider, graph, node):
    facts = service_facts(graph, node)
    reply = provider.complete(
        [{"role": "system", "content": SYSTEM_PROMPT},
         {"role": "user", "content": json.dumps(facts, indent=2)}],
        response_format={"type": "json_object"})
    report = _load_json(reply.content)
    report["problems"] = verify(report, facts)
    return report


def assess_all(provider, graph, log=print):
    """Add an impact assessment to every scanned service in the graph."""
    for node in graph["nodes"]:
        if not node.get("vulns"):
            continue
        log(f"[{node['label']}] assessing impact ...")
        try:
            node["impact"] = assess_service(provider, graph, node)
        except (json.JSONDecodeError, KeyError, TypeError) as err:
            log(f"[{node['label']}] assessment failed: {err}")
            continue
        problems = node["impact"]["problems"]
        log(f"[{node['label']}] risk: {node['impact'].get('risk_level')}"
            + (f"  WARNING: {problems}" if problems else ""))
    return graph