```python
import os
import sys

import requests


SONAR_URL = os.getenv("SONAR_HOST_URL")
TOKEN = os.getenv("SONAR_TOKEN")

METRICS = [
    "coverage",
    "bugs",
    "code_smells",
    "security_hotspots",
]


def fetch_metrics(project_key):
    if not SONAR_URL:
        raise RuntimeError("SONAR_HOST_URL is not set")

    if not TOKEN:
        raise RuntimeError("SONAR_TOKEN is not set")

    url = f"{SONAR_URL.rstrip('/')}/api/measures/component"

    params = {
        "component": project_key,
        "metricKeys": ",".join(METRICS),
    }

    response = requests.get(
        url,
        params=params,
        auth=(TOKEN, ""),
        timeout=30,
    )

    print(f"SonarQube URL: {response.url}")
    print(f"SonarQube status: {response.status_code}")

    if not response.ok:
        print(f"SonarQube response: {response.text}")

    response.raise_for_status()

    data = response.json()

    if "component" not in data:
        raise RuntimeError(
            f"Unexpected SonarQube response: {data}"
        )

    measures = data["component"].get("measures", [])

    return {
        metric["metric"]: metric.get("value", "0")
        for metric in measures
    }

def make_badge(label, value, color="#4c1"):
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="200" height="20">
  <rect width="200" height="20" fill="#555"/>
  <rect x="80" width="120" height="20" fill="{color}"/>
  <text x="40" y="14" fill="#fff" text-anchor="middle"
        font-family="Verdana" font-size="11">{label}</text>
  <text x="140" y="14" fill="#fff" text-anchor="middle"
        font-family="Verdana" font-size="11">{value}</text>
</svg>
"""


def save_badge(project, name, svg):
    out_dir = f"badges/{project}"
    os.makedirs(out_dir, exist_ok=True)

    filename = f"{out_dir}/{name}.svg"

    with open(filename, "w", encoding="utf-8") as file:
        file.write(svg)

    print(f"Created {filename}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python generate_badges.py <project_key>")
        sys.exit(1)

    project_key = sys.argv[1]

    print(f"Generating badges for project: {project_key}")
    print(f"SonarQube: {SONAR_URL}")
    print(f"SONAR_TOKEN set: {'yes' if TOKEN else 'no'}")

    metrics = fetch_metrics(project_key)

    coverage = metrics.get("coverage", "0")
    bugs = metrics.get("bugs", "0")
    code_smells = metrics.get("code_smells", "0")
    security_hotspots = metrics.get("security_hotspots", "0")

    save_badge(
        project_key,
        "coverage",
        make_badge("coverage", f"{coverage}%"),
    )

    save_badge(
        project_key,
        "bugs",
        make_badge("bugs", bugs),
    )

    save_badge(
        project_key,
        "code_smells",
        make_badge("smells", code_smells),
    )

    save_badge(
        project_key,
        "security_hotspots",
        make_badge("hotspots", security_hotspots),
    )


if __name__ == "__main__":
    main()
```
