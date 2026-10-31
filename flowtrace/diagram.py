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
  .legend span { margin-right: 14px; font-size: 13px; white-space: nowrap; }
  .key { display: inline-block; width: 12px; height: 12px; border: 1px solid;
         margin-right: 4px; vertical-align: middle; }
  .line { display: inline-block; width: 18px; height: 3px; margin-right: 4px;
          vertical-align: middle; }
  .summary { font-size: 15px; font-weight: 600; margin: 4px 0 8px; }
  .tag { display: inline-block; padding: 2px 10px; border-radius: 10px;
         background: #e8eefc; color: #1a3f8f; font-size: 12px; }
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
    <span><span class="line" style="background:#3b6fd8"></span>Data flow</span>
    <span><span class="line" style="background:#d93025;height:4px"></span>Sensitive data flow</span>
  </div>
  <p class="hint">Click an arrow to see what data moves and the code that proves it.
  Hover over a box to see every name that system was found under.</p>
  <div id="info"></div>
</div>
<script>
const graph = __GRAPH__;
const labels = Object.fromEntries(graph.nodes.map(n => [n.id, n.label]));

const nodes = new vis.DataSet(graph.nodes.map(n => ({
  id: n.id, label: n.label, shape: "box", margin: 10,
  color: n.is_repo ? {background: "#d6e6ff", border: "#3b6fd8"}
                   : {background: "#f2f2f2", border: "#999999"},
  title: "Seen as: " + n.names_seen.join(", ")
})));
const edges = new vis.DataSet(graph.edges.map((e, i) => ({
  id: i, from: e.source, to: e.destination, label: e.mechanism, arrows: "to",
  title: (e.data || []).join("; "),
  color: e.sensitive ? {color: "#d93025", highlight: "#a50e0e"}
                     : {color: "#3b6fd8", highlight: "#1a3f8f"},
  width: e.sensitive ? 3 : 1.5,
  font: {size: 11, align: "middle"}
})));

// Build the details panel with textContent so code can never break the page.
function show(e) {
  const info = document.getElementById("info");
  info.innerHTML = "";
  const add = (tag, text, cls) => {
    const el = document.createElement(tag);
    el.textContent = text;
    if (cls) el.className = cls;
    info.appendChild(el);
  };
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
  if (params.edges.length && !params.nodes.length) show(graph.edges[params.edges[0]]);
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