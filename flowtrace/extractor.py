import json

from .models import CONFIDENCE_LEVELS, DATA_CATEGORIES, MECHANISMS, DataFlow

MAX_PROMPT_CHARS = 400_000  # stay well inside the model's context window

SYSTEM_PROMPT = f"""You are FlowTrace, an expert software architect who maps how data moves between systems.

You will receive every relevant file from ONE repository. Each line is numbered.
Identify every data flow where data moves between this repository's system and another system at runtime.

Rules for finding flows:
- Only report flows that the code clearly shows. Never guess or invent.
- Only runtime flows: ignore build-time downloads (Dockerfile installs, package fetches), tests and sample data.
- Ignore health checks and liveness probes.
- Every flow needs evidence: the exact file path and line numbers, copied from the numbered listing.
  Cite each code location only once per flow.
- Include outgoing flows (this system sends data) and incoming flows (this system receives data, e.g. an API endpoint).
  For incoming flows where the caller is unknown, use "unknown client" as the source.
- Do not report function calls inside the same system.

Rules for naming systems:
- Call this repository's own system by the repository name you are given.
- Name other systems by their short service, host or product name, e.g. "catalogue", "mysql", "rabbitmq",
  "PayPal", "Instana monitoring".
- Never use a full URL, a code function name or an environment variable as a name
  when the real system is clear from the code.

Rules for describing the data:
- "data": a short plain-English summary of WHAT data moves, at most 8 words.
  Describe the data itself, not the endpoint or the code.
- "fields": the main data items sent, e.g. ["order_id", "total", "email"].
- "category": exactly one of: {", ".join(DATA_CATEGORIES)}
  personal = names, emails, addresses, user ids; payment = card or billing data;
  credentials = passwords, tokens, keys; business = orders, products, carts, ratings;
  operational = metrics, logs, monitoring events.
- If a flow carries several kinds of data, use the most sensitive category.

BAD data description: "PUT /api/rate/{{sku}}/{{score}} rating submission request"
GOOD data description: "data": "Product ratings", "fields": ["sku", "score"], "category": "business"

mechanism must be one of: {", ".join(MECHANISMS)}
confidence must be one of: {", ".join(CONFIDENCE_LEVELS)}

Respond with JSON only, in exactly this shape:
{{"flows": [{{"source": "...", "destination": "...", "data": "short summary",
  "fields": ["..."], "category": "...", "mechanism": "...", "confidence": "...",
  "evidence": [{{"file": "path/in/repo", "start_line": 1, "end_line": 3, "snippet": "..."}}]}}]}}
If there are no data flows, respond with {{"flows": []}}."""


def format_files(files):
    """Turn the files into one numbered listing the model can cite."""
    parts = []
    for f in files:
        numbered = "\n".join(f"{i:>4} | {line}"
                             for i, line in enumerate(f.content.splitlines(), start=1))
        parts.append(f"=== FILE: {f.path} ({f.kind}, {f.language}) ===\n{numbered}")
    text = "\n\n".join(parts)
    if len(text) > MAX_PROMPT_CHARS:
        raise ValueError(f"Repository too large for one request ({len(text)} chars)")
    return text


def build_messages(repo_name, files):
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Repository name: {repo_name}\n\n{format_files(files)}"},
    ]


def verify_evidence(flow, file_lines):
    """Check cited files and lines are real, then replace snippets with the actual code."""
    problems = []
    for e in flow.evidence:
        lines = file_lines.get(e.file)
        if lines is None:
            problems.append(f"evidence file not found: {e.file}")
        elif e.end_line > len(lines):
            problems.append(f"line {e.end_line} is past the end of {e.file} ({len(lines)} lines)")
        else:
            e.snippet = "\n".join(lines[e.start_line - 1:e.end_line])
    return problems


def parse_response(text, repo_name, files):
    """Turn the model's reply into verified flows and rejected flows (with reasons)."""
    text = text.strip()
    if text.startswith("```"):  # remove ```json fences if the model adds them
        text = text.strip("`").removeprefix("json").strip()
    data = json.loads(text)
    raw_flows = data.get("flows", []) if isinstance(data, dict) else data

    file_lines = {f.path: f.content.splitlines() for f in files}
    accepted, rejected = [], []
    for raw in raw_flows:
        try:
            flow = DataFlow.from_dict(raw, repo_name)
            problems = flow.validate() or verify_evidence(flow, file_lines)
        except (TypeError, ValueError, KeyError) as err:
            rejected.append((raw, [f"malformed flow: {err}"]))
            continue
        if problems:
            rejected.append((raw, problems))
        else:
            accepted.append(flow)
    return accepted, rejected


def extract_flows(provider, repo_name, files):
    """Ask the model for the repository's data flows and verify the answer."""
    reply = provider.complete(build_messages(repo_name, files),
                              response_format={"type": "json_object"})
    return parse_response(reply.content, repo_name, files)