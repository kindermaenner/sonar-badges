import os
import sys
import requests

SONAR_URL = os.getenv("SONAR_HOST_URL")
TOKEN = os.getenv("SONAR_TOKEN")
DUPLICATION_GOOD_THRESHOLD = 3.0

# All metrics we need from SonarQube
METRICS = [
    "coverage",
    "bugs",
    "vulnerabilities",
    "code_smells",
    "security_hotspots",
    "duplicated_lines_density",
    "reliability_rating",
    "security_rating",
    "sqale_rating",
]

# Icons for each badge
ICONS = {
    "coverage": "📊",
    "bugs": "🐞",
    "vulnerabilities": "🔒",
    "code_smells": "💨",
    "security_hotspots": "🔥",
    "duplicated_lines_density": "🔁",
}

# Colors for A–E ratings
RATING_COLORS = {
    "A": "#4c1",
    "B": "#97CA00",
    "C": "#dfb317",
    "D": "#fe7d37",
    "E": "#e05d44",
}

def color_for_duplications(value):
    try:
        v = float(value)
    except ValueError:
        return "#555"

    if v <= DUPLICATION_GOOD_THRESHOLD:
        return "#4c1"       # sehr gut
    elif v <= DUPLICATION_GOOD_THRESHOLD + 2:
        return "#97CA00"    # gut
    elif v <= 10:
        return "#dfb317"    # mittel
    elif v <= 20:
        return "#fe7d37"    # schlecht
    else:
        return "#e05d44"    # sehr schlecht

def color_for_coverage(value):
    """Dynamic color scale for coverage & duplications."""
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
    """Fetch all metrics from SonarQube."""
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

def extract_rating(value):
    """Extract the rating letter from values like '0A', '21C', '0.0%E'."""
    if not value:
        return None
    return value[-1] if value[-1] in "ABCDE" else None

def make_badge(label, value, color):
    """Generate compact SVG badge with rounded corners."""
    label_text = f"{ICONS.get(label, '')} {label}"
    value_text = str(value)

    # Compact width calculation
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
    """Write badge SVG to disk."""
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

    # Coverage (value)
    coverage = metrics.get("coverage", "0")
    save_badge(
        project_key,
        "coverage",
        make_badge("coverage", f"{coverage}%", color_for_coverage(coverage)),
    )

    # Bugs (rating)
    bugs_rating = extract_rating(metrics.get("reliability_rating"))
    save_badge(
        project_key,
        "bugs",
        make_badge("bugs", bugs_rating, RATING_COLORS.get(bugs_rating, "#555")),
    )

    # Vulnerabilities (rating)
    vuln_rating = extract_rating(metrics.get("security_rating"))
    save_badge(
        project_key,
        "vulnerabilities",
        make_badge("vulnerabilities", vuln_rating, RATING_COLORS.get(vuln_rating, "#555")),
    )

    # Code Smells (rating)
    smells_rating = extract_rating(metrics.get("sqale_rating"))
    save_badge(
        project_key,
        "code_smells",
        make_badge("code_smells", smells_rating, RATING_COLORS.get(smells_rating, "#555")),
    )

    # Hotspots Reviewed (rating)
    hotspots_rating = extract_rating(metrics.get("security_hotspots_reviewed_rating"))
    if hotspots_rating:
        save_badge(
            project_key,
            "security_hotspots",
            make_badge("security_hotspots", hotspots_rating, RATING_COLORS.get(hotspots_rating, "#555")),
        )

    # Duplications (value)
    dups = metrics.get("duplicated_lines_density", "0")
    save_badge(
        project_key,
        "duplicated_lines_density",
        make_badge("duplicated_lines_density", f"{dups}%", color_for_duplications(dups)),
    )



if __name__ == "__main__":
    main()
