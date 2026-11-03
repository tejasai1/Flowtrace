import html
import json
from pathlib import Path

TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>__TITLE__</title>
<script src="https://unpkg.com/vis-network@9.1.9/standalone/umd/vis-network.min.js"></script>
<style>
  body { margin: 0; font-family: system-ui, sans-serif; display: flex; height: 100vh; }
  #graph { flex: 2; border-right: 1px solid #ddd; }
  #details { flex: 1; padding: 16px; overflow-y: auto; background: #fafafa; }
  h1 { font-size: 18px; margin: 0 0 8px; }
  h2 { font-size: 16px; margin: 16px 0 4px; }
  .hint { color: #666; font-size: 14px; }
  .legend span { margin-right: 14px; font-size: 13px; white-space: nowrap; line-height: 1.8; }
  .key { display: inline-block; width: 12px; height: 12px; border: 1px solid;
         margin-right: 4px; vertical-align: middle; }
  .line { display: inline-block; width: 18px; height: 3px; margin-right: 4px;
          vertical-align: middle; }
  .summary { font-size: 15px; font-weight: 600; margin: 4px 0 8px; }
  .tag { display: inline-block; padding: 2px 10px; border-radius: 10px;
         background: #e8eefc; color: #1a3f8f; font-size: 12px; margin: 2px 0; }
  .tag.sensitive { background: #fde7e7; color: #a50e0e; font-weight: 600; }
  .ev-file { font-size: 13px; color: #444; margin-top: 12px; }
  pre { background: #1e1e1e; color: #ddd; padding: 8px; border-radius: 4px;
        overflow-x: auto; font-size: 12px; }
</style>
</head>
<body>
<div id="graph"></div>
<div id="details">
  <h1>__TITLE__</h1>
  <div class="legend">
    <span><span class="key" style="background:#d6e6ff;border-color:#3b6fd8"></span>Analyzed service</span>
    <span><span class="key" style="background:#f2f2f2;border-color:#999"></span>External system</span>
    <span><span class="key" style="background:#fde0dc;border-color:#b3261e"></span>Critical vulnerabilities</span>
    <span><span class="key" style="background:#fff0db;border-color:#e8710a"></span>High vulnerabilities</span>
    <span><span class="line" style="background:#3b6fd8"></span>Data flow</span>
    <span><span class="line" style="background:#d93025;height:4px"></span>Sensitive data flow</span>
  </div>
  <p class="hint">Click an arrow to see what data moves and the code that proves it.
  Click a service to see its vulnerabilities and the sensitive data flowing through it.</p>
  <div id="info"></div>
</div>
<script>
const graph = __GRAPH__;
const labels = Object.fromEntries(graph.nodes.map(n => [n.id, n.label]));
const SEVERITY_COLORS = {
  Critical: {background: "#fde0dc", border: "#b3261e"},
  High: {background: "#fff0db", border: "#e8710a"},
  Medium: {background: "#fffbe6", border: "#c9a400"}
};

function worstSeverity(n) {
  if (!n.vulns) return null;
  const c = n.vulns.by_severity;
  return ["Critical", "High", "Medium"].find(s => c[s] > 0) || null;
}

const nodes = new vis.DataSet(graph.nodes.map(n => {
  const worst = worstSeverity(n);
  const c = n.vulns ? n.vulns.by_severity : null;
  return {
    id: n.id, shape: "box", margin: 10,
    label: c ? n.label + "\\n" + c.Critical + " critical \\u00b7 " + c.High + " high" : n.label,
    color: worst ? SEVERITY_COLORS[worst]
         : n.is_repo ? {background: "#d6e6ff", border: "#3b6fd8"}
                     : {background: "#f2f2f2", border: "#999999"},
    borderWidth: worst ? 2 : 1,
    title: "Seen as: " + n.names_seen.join(", ")
  };
}));
const edges = new vis.DataSet(graph.edges.map((e, i) => ({
  id: i, from: e.source, to: e.destination, label: e.mechanism, arrows: "to",
  title: (e.data || []).join("; "),
  color: e.sensitive ? {color: "#d93025", highlight: "#a50e0e"}
                     : {color: "#3b6fd8", highlight: "#1a3f8f"},
  width: e.sensitive ? 3 : 1.5,
  font: {size: 11, align: "middle"}
})));

// Build the details panel with textContent so code can never break the page.
const info = document.getElementById("info");
function add(tag, text, cls) {
  const el = document.createElement(tag);
  el.textContent = text;
  if (cls) el.className = cls;
  info.appendChild(el);
}

function showEdge(e) {
  info.innerHTML = "";
  add("h2", labels[e.source] + " \\u2192 " + labels[e.destination]);
  add("p", (e.data || []).join("; ") || "(no description)", "summary");
  const category = e.category || "uncategorized";
  add("span", e.sensitive ? "Sensitive: " + category : category,
      e.sensitive ? "tag sensitive" : "tag");
  if ((e.fields || []).length) add("p", "Sends: " + e.fields.join(", "));
  if ((e.returns || []).length) add("p", "Returns: " + e.returns.join(", "));
  add("p", "Mechanism: " + e.mechanism);
  add("p", "Found in: " + e.repos.join(", "));
  e.evidence.forEach(ev => {
    add("div", ev.repo + " / " + ev.file + "  (lines " + ev.start_line +
               "\\u2013" + ev.end_line + ")", "ev-file");
    add("pre", ev.snippet || "(no snippet)");
  });
}

function showNode(n) {
  info.innerHTML = "";
  add("h2", n.label);
  if (!n.vulns) {
    add("p", n.is_repo ? "No vulnerability scan for this service." : "External system (not scanned).");
    return;
  }
  const v = n.vulns, c = v.by_severity;
  add("p", v.unique_vulnerabilities + " known vulnerabilities (" + v.app_level +
           " in the service's own libraries)", "summary");
  add("p", "Critical " + c.Critical + " \\u00b7 High " + c.High + " \\u00b7 Medium " +
           c.Medium + " \\u00b7 Low " + c.Low);

  const sensitive = graph.edges.filter(e => e.sensitive &&
                                       (e.source === n.id || e.destination === n.id));
  if (sensitive.length) {
    add("h2", "Sensitive data flowing through it");
    sensitive.forEach(e => add("p", labels[e.source] + " \\u2192 " + labels[e.destination] +
                               ": " + e.category + " (" + (e.data || []).join("; ") + ")",
                               "tag sensitive"));
  }

  add("h2", "Most serious vulnerabilities");
  v.top.forEach(t => {
    add("div", "[" + t.severity + "] " + t.id + " \\u2014 " +
               (t.app_level ? "app library" : "system package"), "ev-file");
    add("pre", t.packages.join("\\n") + "\\nFixed in: " + (t.fixed_in.join(", ") || "no fix yet"));
  });
}

const network = new vis.Network(document.getElementById("graph"), {nodes, edges}, {
  layout: {randomSeed: 7, improvedLayout: true},
  physics: {
    solver: "forceAtlas2Based",
    forceAtlas2Based: {gravitationalConstant: -90, springLength: 170,
                       springConstant: 0.04, avoidOverlap: 0.8},
    stabilization: {iterations: 500}
  },
  edges: {smooth: {type: "continuous"}}
});
// Once the layout settles, freeze it and fit everything on screen.
network.once("stabilizationIterationsDone", () => {
  network.setOptions({physics: false});
  network.fit();
});
network.on("click", params => {
  if (params.nodes.length) showNode(graph.nodes.find(n => n.id === params.nodes[0]));
  else if (params.edges.length) showEdge(graph.edges[params.edges[0]]);
});
</script>
</body>
</html>"""


def render_html(graph, title="FlowTrace data flow map"):
    """Turn a graph from build_graph() into a standalone interactive web page."""
    data = json.dumps(graph).replace("</", "<\\/")  # keep code snippets from closing the script tag
    return TEMPLATE.replace("__TITLE__", html.escape(title)).replace("__GRAPH__", data)


def write_html(graph, path, title="FlowTrace data flow map"):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_html(graph, title), encoding="utf-8")
    return path