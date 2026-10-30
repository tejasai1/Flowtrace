import json
from pathlib import Path

from .diagram import write_html
from .extractor import extract_flows
from .graph import build_graph
from .reader import read_repository


def find_repositories(workspace, only=None):
    """Every non-hidden folder inside the workspace is one repository.
    If 'only' is given, analyze just those folders."""
    root = Path(workspace).resolve()
    if not root.is_dir():
        raise FileNotFoundError(f"Workspace folder not found: {root}")
    repos = [p for p in sorted(root.iterdir())
             if p.is_dir() and not p.name.startswith(".")]
    if only:
        missing = set(only) - {p.name for p in repos}
        if missing:
            raise ValueError(f"Not found in workspace: {sorted(missing)}")
        repos = [p for p in repos if p.name in set(only)]
    if not repos:
        raise ValueError(f"No repository folders found in {root}")
    return repos


def run(workspace, provider, output_dir="output", aliases=None, log=print, only=None):
    """Read every repository, extract and verify flows, build the map, save results."""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    repos = find_repositories(workspace, only)
    all_flows, report = [], {}

    for repo_path in repos:
        name = repo_path.name
        files = read_repository(repo_path)
        log(f"[{name}] read {len(files)} files")
        if not files:
            report[name] = {"files": 0, "accepted": 0, "rejected": []}
            continue
        accepted, rejected = extract_flows(provider, name, files)
        log(f"[{name}] {len(accepted)} flows accepted, {len(rejected)} rejected")
        all_flows += accepted
        report[name] = {"files": len(files), "accepted": len(accepted),
                        "rejected": [{"flow": raw, "problems": problems}
                                     for raw, problems in rejected]}

    graph = build_graph(all_flows, [r.name for r in repos], aliases)

    # Plain JSON output, so other tools (like the capstone app) can use the results.
    (out / "flows.json").write_text(
        json.dumps([f.to_dict() for f in all_flows], indent=2), encoding="utf-8")
    (out / "graph.json").write_text(json.dumps(graph, indent=2), encoding="utf-8")
    (out / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    title = f"Data flow map: {Path(workspace).resolve().name}"
    diagram = write_html(graph, out / "diagram.html", title)

    log(f"\nSaved flows.json, graph.json, report.json and {diagram.name} in {out.resolve()}")
    return graph, report