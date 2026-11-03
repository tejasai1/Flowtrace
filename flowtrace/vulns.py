import json
import shutil
import subprocess
from pathlib import Path

SEVERITY_ORDER = ["Critical", "High", "Medium", "Low", "Negligible", "Unknown"]
# Package types that are an application's own libraries. Everything else
# (Debian packages, programs found in the image) counts as system software.
APP_PACKAGE_TYPES = {"python", "npm", "java-archive", "go-module", "php-composer",
                     "gem", "dotnet", "rust-crate"}


def run_grype(target, cache_file=None):
    """Scan a target with Grype and return its JSON report.
    If cache_file exists, reuse it instead of scanning again (scans are slow)."""
    if cache_file and Path(cache_file).exists():
        return json.loads(Path(cache_file).read_text(encoding="utf-8"))
    grype = shutil.which("grype")
    if not grype:
        raise RuntimeError("Grype not found: add its folder to PATH first")
    result = subprocess.run([grype, target, "-o", "json", "-q"],
                            capture_output=True, text=True, encoding="utf-8")
    if result.returncode != 0:
        raise RuntimeError(f"Grype failed for {target}: {result.stderr.strip()[:500]}")
    if cache_file:
        Path(cache_file).parent.mkdir(parents=True, exist_ok=True)
        Path(cache_file).write_text(result.stdout, encoding="utf-8")
    return json.loads(result.stdout)


def _rank(severity):
    return SEVERITY_ORDER.index(severity) if severity in SEVERITY_ORDER else len(SEVERITY_ORDER)


def summarize(report, top=5):
    """Count each vulnerability once, by severity, and pick the most serious ones."""
    vulns = {}
    for match in report.get("matches", []):
        v, pkg = match["vulnerability"], match["artifact"]
        entry = vulns.setdefault(v["id"], {
            "id": v["id"], "severity": v.get("severity", "Unknown"),
            "packages": set(), "app_level": False,
            "fixed_in": v.get("fix", {}).get("versions", [])})
        entry["packages"].add(f"{pkg['name']} {pkg['version']}")
        if pkg.get("type") in APP_PACKAGE_TYPES:
            entry["app_level"] = True

    counts = {s: 0 for s in SEVERITY_ORDER}
    for e in vulns.values():
        counts[e["severity"] if e["severity"] in counts else "Unknown"] += 1

    # Most severe first; within the same severity, the app's own libraries first.
    ranked = sorted(vulns.values(), key=lambda e: (_rank(e["severity"]), not e["app_level"]))
    serious = [{"id": e["id"], "severity": e["severity"], "app_level": e["app_level"],
                "packages": sorted(e["packages"])[:3], "fixed_in": e["fixed_in"][:3]}
               for e in ranked if e["severity"] in ("Critical", "High")][:top]

    return {"unique_vulnerabilities": len(vulns), "by_severity": counts,
            "app_level": sum(e["app_level"] for e in vulns.values()), "top": serious}