import re
from dataclasses import asdict

# Endings that don't change which system a name refers to.
SUFFIXES = ("-base-url", "-api-url", "-url", "-uri", "-host", "-endpoint",
            "-addr", "-service", "-svc")
URL_RE = re.compile(r"[a-z][a-z0-9+.-]*://[^\s)\"'>]+")
UNKNOWN = "unknown-client"
# Higher number = more sensitive; an arrow shows its most sensitive category.
CATEGORY_RANK = {"credentials": 5, "payment": 4, "personal": 3,
                 "business": 2, "operational": 1}


def normalize_name(name):
    """Reduce different spellings of a system name to one matching key."""
    key = name.strip().lower()
    url = URL_RE.search(key)
    if url:                                 # "payment gateway (https://paypal.com/)"
        key = url.group(0)                  #   -> "https://paypal.com/"
    key = re.sub(r"^[a-z][a-z0-9+.-]*://", "", key)  # remove http://, postgres://, ...
    key = key.split("/")[0]                 # remove any path like /charge
    key = re.sub(r":\d+$", "", key)         # remove a port like :8000
    key = key.removeprefix("www.")
    key = re.sub(r"[_\s]+", "-", key)       # PAYMENTS_URL -> payments-url
    changed = True
    while changed:                          # strip endings, possibly several
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
            "data": [], "fields": [], "category": "", "sensitive": False,
            "repos": [], "evidence": []})
        if f.data and f.data not in edge["data"]:
            edge["data"].append(f.data)
        for name in f.fields:
            if name not in edge["fields"]:
                edge["fields"].append(name)
        if CATEGORY_RANK.get(f.category, 0) > CATEGORY_RANK.get(edge["category"], 0):
            edge["category"] = f.category
        edge["sensitive"] = edge["sensitive"] or f.sensitive
        if f.repo not in edge["repos"]:
            edge["repos"].append(f.repo)
        # Add each piece of evidence only once.
        seen = {(e["repo"], e["file"], e["start_line"], e["end_line"])
                for e in edge["evidence"]}
        for e in f.evidence:
            k = (f.repo, e.file, e.start_line, e.end_line)
            if k not in seen:
                seen.add(k)
                edge["evidence"].append({"repo": f.repo, **asdict(e)})

    # Drop "unknown client -> X" when a known system already sends data to X that way.
    known = {(e["destination"], e["mechanism"])
             for e in edges.values() if e["source"] != UNKNOWN}
    edge_list = [e for e in edges.values()
                 if not (e["source"] == UNKNOWN
                         and (e["destination"], e["mechanism"]) in known)]

    # Keep every analyzed repository, plus any system still connected to something.
    used = {e["source"] for e in edge_list} | {e["destination"] for e in edge_list}
    node_list = [n for n in nodes.values() if n["is_repo"] or n["id"] in used]
    for node in node_list:
        node["names_seen"] = sorted(node["names_seen"])
    return {"nodes": node_list, "edges": edge_list}