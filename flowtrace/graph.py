import re
from dataclasses import asdict

# Endings that don't change which system a name refers to.
SUFFIXES = ("-base-url", "-api-url", "-url", "-uri", "-host", "-endpoint",
            "-addr", "-service", "-svc")


def normalize_name(name):
    """Reduce different spellings of a system name to one matching key."""
    key = name.strip().lower()
    key = re.sub(r"^[a-z]+://", "", key)   # remove http://, postgres://, ...
    key = key.split("/")[0]                # remove any path like /charge
    key = re.sub(r":\d+$", "", key)        # remove a port like :8000
    key = re.sub(r"[_\s]+", "-", key)      # PAYMENTS_URL -> payments-url
    changed = True
    while changed:                         # strip endings, possibly several
        changed = False
        for suffix in SUFFIXES:
            if key.endswith(suffix) and len(key) > len(suffix):
                key = key[: -len(suffix)]
                changed = True
    return key


def build_graph(flows, repo_names, aliases=None):
    """Merge flows from many repositories into one map of systems and flows."""
    aliases = aliases or {}
    alias_map = {normalize_name(k): normalize_name(v) for k, v in aliases.items()}
    alias_labels = {normalize_name(v): v for v in aliases.values()}
    repo_labels = {normalize_name(r): r for r in repo_names}
    nodes, edges = {}, {}

    def node_for(name):
        key = normalize_name(name)
        key = alias_map.get(key, key)
        if key not in nodes:
            clean = key if "://" in name else name  # show a host, not a full URL
            label = repo_labels.get(key) or alias_labels.get(key) or clean
            nodes[key] = {"id": key, "label": label,
                          "is_repo": key in repo_labels, "names_seen": set()}
        nodes[key]["names_seen"].add(name)
        return key

    for f in flows:
        src, dst = node_for(f.source), node_for(f.destination)
        if src == dst:
            continue  # a system talking to itself is not a data flow
        edge = edges.setdefault((src, dst, f.mechanism), {
            "source": src, "destination": dst, "mechanism": f.mechanism,
            "data": [], "repos": [], "evidence": []})
        if f.data not in edge["data"]:
            edge["data"].append(f.data)
        if f.repo not in edge["repos"]:
            edge["repos"].append(f.repo)
        edge["evidence"] += [{"repo": f.repo, **asdict(e)} for e in f.evidence]

    for node in nodes.values():
        node["names_seen"] = sorted(node["names_seen"])
    return {"nodes": list(nodes.values()), "edges": list(edges.values())}