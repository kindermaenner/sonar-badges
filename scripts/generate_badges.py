import requests
import json
import os
import sys

SONAR_URL = os.getenv("SONAR_HOST_URL")
TOKEN = os.getenv("SONAR_TOKEN")

METRICS = ["coverage", "bugs", "code_smells", "security_hotspots"]

def fetch_metrics(project_key):
    url = f"{SONAR_URL}/api/measures/component"
    params = {
        "component": project_key,
        "metricKeys": ",".join(METRICS)
    }
    response = requests.get(url, auth=(TOKEN, ""))
    response.raise_for_status()
    data = response.json()["component"]["measures"]
    return {m["metric"]: m.get("value", "0") for m in data}

def make_badge(label, value, color="#4c1"):
    return f"""
<svg xmlns="http://www.w3.org/2000/svg" width="140" height="20">
  <rect width="70" height="20" fill="#555"/>
  <rect x="70" width="70" height="20" fill="{color}"/>
  <text x="35" y="14" fill="#fff" font-size="11" text-anchor="middle">{label}</text>
  <text x="105" y="14" fill="#fff" font-size="11" text-anchor="middle">{value}</text>
</svg>
"""

def save_badge(project, name, svg):
    out_dir = f"badges/{project}"
    os.makedirs(out_dir, exist_ok=True)
    with open(f"{out_dir}/{name}.svg", "w") as f:
        f.write(svg)

def main():
    if len(sys.argv) < 2:
        print("Usage: python generate.py <project_key>")
        sys.exit(1)

    project_key = sys.argv[1]
    metrics = fetch_metrics(project_key)

    save_badge(project_key, "coverage", make_badge("coverage", metrics["coverage"] + "%"))
    save_badge(project_key, "bugs", make_badge("bugs", metrics["bugs"]))
    save_badge(project_key, "code_smells", make_badge("smells", metrics["code_smells"]))
    save_badge(project_key, "security_hotspots", make_badge("hotspots", metrics["security_hotspots"]))

if __name__ == "__main__":
    main()
