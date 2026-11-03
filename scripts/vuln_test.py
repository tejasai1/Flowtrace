from flowtrace.vulns import run_grype, summarize

IMAGE = "registry:robotshop/rs-payment:2.1.0"
report = run_grype(IMAGE, cache_file="output/vulns/payment.json")
s = summarize(report)

print(f"Unique vulnerabilities: {s['unique_vulnerabilities']} "
      f"({s['app_level']} in the app's own libraries)")
for severity, n in s["by_severity"].items():
    print(f"  {severity:10} {n}")

print("\nMost serious:")
for v in s["top"]:
    where = "app library" if v["app_level"] else "system package"
    fix = ", ".join(v["fixed_in"]) or "no fix yet"
    print(f"  [{v['severity']}] {v['id']} in {', '.join(v['packages'])} ({where}); fixed in: {fix}")