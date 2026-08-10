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
    "reliability_rating",
    "security_rating",
    "sqale_rating",
]

ICONS = {
    "coverage": "📊",
    "bugs": "🐞",
    "code_smells": "💨",
    "security_hotspots": "🔥",
    "reliability_rating": "🐞",
    "security_rating": "🔒",
    "sqale_rating": "💨",
}

RATING_COLORS = {
    "A": "#4c1",
    "B": "#97CA00",
    "C": "#dfb317",
    "D": "#fe7d37",
    "E": "#e05d44",
}


def color_for_coverage(value):
    try:
        v = float(value)
    except ValueError:
        return "#555"

    if v >= 80:
        return "#4c1"
    elif v >= 60:
        return "#97CA00"
    elif v >= 40:
        return "#dfb317"
    elif v >= 20:
        return "#fe7d37"
    else:
        return "#e05d44"


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
        raise RuntimeError(f"Unexpected SonarQube response: {data}")

    measures = data["component"].get("measures", [])

    return {m["metric"]: m.get("value", "0") for m in measures}


def make_badge(label, value, color):
    # kompakte Breite berechnen
    label_text = f"{ICONS.get(label, '')} {label}"
    value_text = str(value)

    label_width = 7 * len(label_text) + 20
    value_width = 7 * len(value_text) + 20
    total_width = label_width + value_width

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{total_width}" height="20">
  <rect width="{total_width}" height="20" rx="3" ry="3" fill="#555"/>
  <rect x="{label_width}" width="{value_width}" height="20" rx="3" ry="3" fill="{color}"/>
  <text x="10" y="14" fill="#fff" font-family="Verdana" font-size="11">{label_text}</text>
  <text x="{label_width + 10}" y="14" fill="#fff" font-family="Verdana" font-size="11">{value_text}</text>
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

    # Coverage
    coverage = metrics.get("coverage", "0")
    save_badge(
        project_key,
        "coverage",
        make_badge("coverage", f"{coverage}%", color_for_coverage(coverage)),
    )

    # Bugs
    bugs = metrics.get("bugs", "0")
    rating_bugs = metrics.get("reliability_rating", None)
    color_bugs = RATING_COLORS.get(rating_bugs, "#555")
    save_badge(
        project_key,
        "bugs",
        make_badge("bugs", bugs, color_bugs),
    )

    # Code Smells
    smells = metrics.get("code_smells", "0")
    rating_smells = metrics.get("sqale_rating", None)
    color_smells = RATING_COLORS.get(rating_smells, "#555")
    save_badge(
        project_key,
        "code_smells",
        make_badge("code_smells", smells, color_smells),
    )

    # Security Hotspots
    hotspots = metrics.get("security_hotspots", "0")
    rating_sec = metrics.get("security_rating", None)
    color_sec = RATING_COLORS.get(rating_sec, "#555")
    save_badge(
        project_key,
        "security_hotspots",
        make_badge("security_hotspots", hotspots, color_sec),
    )


if __name__ == "__main__":
    main()
