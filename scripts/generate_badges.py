import os
import sys
import requests
import json

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
    "security_review_rating",
    "security_hotspots_reviewed_rating",
]

# Monochrome SVG paths for each badge
ICONS = {
    "coverage": "M12 20V10M18 20V4M6 20v-4",
    "bugs": "M8 7V3M16 7V3M7 11H17M8 21v-4a4 4 0 1 1 8 0v4",
    "vulnerabilities": "M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z",
    "code_smells": "M17 20c0-2.5-2-4.5-4.5-4.5S8 17.5 8 20M13 15c0-2.2-1.8-4-4-4s-4 1.8-4 4",
    "security_hotspots": "M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z",
    "duplicated_lines_density": "M7 7h10v10H7zM11 11h10v10H11z",
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
    print("SonarQube API Response:")
    print(json.dumps(data, indent=2))

    if "component" not in data:
        raise RuntimeError(f"Unexpected SonarQube response: {data}")

    measures = data["component"].get("measures", [])

    return {m["metric"]: m.get("value", "0") for m in measures}

def extract_rating(value):
    """Extract the rating letter (A-E) from Sonar metrics."""
    if not value:
        return None

    # Map numeric ratings (1.0 -> A, 2.0 -> B, etc.)
    mapping = {"1.0": "A", "2.0": "B", "3.0": "C", "4.0": "D", "5.0": "E",
               "1": "A", "2": "B", "3": "C", "4": "D", "5": "E"}

    val_str = str(value)
    if val_str in mapping:
        return mapping[val_str]

    # Fallback to the last character if it's A-E
    char = val_str[-1].upper()
    return char if char in "ABCDE" else None

def make_badge(label, value, color):
    """Generate compact SVG badge with rounded corners and monochrome icon."""
    icon_key = label.lower().replace(" ", "_")
    if icon_key == "hotspots_reviewed":
        icon_key = "security_hotspots"
    if icon_key == "duplications":
        icon_key = "duplicated_lines_density"

    icon_path = ICONS.get(icon_key, "")
    has_icon = bool(icon_path)
    icon_offset = 20 if has_icon else 0

    label_text = label
    value_text = str(value)

    # Compact width calculation
    label_width = 7 * len(label_text) + 20 + icon_offset
    value_width = 7 * len(value_text) + 20
    total_width = label_width + value_width

    icon_svg = ""
    if has_icon:
        # Drawing icon at x=7, y=3 with scaling
        style = 'stroke="#fff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" fill="none"'
        if icon_key in ["security_hotspots", "duplicated_lines_density"]:
             style = 'fill="#fff"'
        
        icon_svg = f'<g transform="translate(7, 3) scale(0.6)"><path d="{icon_path}" {style}/></g>'

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{total_width}" height="20">
  <rect width="{total_width}" height="20" rx="3" ry="3" fill="#555"/>
  <rect x="{label_width}" width="{value_width}" height="20" rx="3" ry="3" fill="{color}"/>
  {icon_svg}
  <text x="{10 + icon_offset}" y="14" fill="#fff" font-family="Verdana" font-size="11">{label_text}</text>
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

    # Bugs (Count + Rating for color)
    bugs_count = metrics.get("bugs", "0")
    bugs_rating = extract_rating(metrics.get("reliability_rating"))
    save_badge(
        project_key,
        "bugs",
        make_badge("bugs", bugs_count, RATING_COLORS.get(bugs_rating, "#555")),
    )

    # Vulnerabilities (Count + Rating for color)
    vuln_count = metrics.get("vulnerabilities", "0")
    vuln_rating = extract_rating(metrics.get("security_rating"))
    save_badge(
        project_key,
        "vulnerabilities",
        make_badge("vulnerabilities", vuln_count, RATING_COLORS.get(vuln_rating, "#555")),
    )

    # Code Smells (Count + Rating for color)
    smells_count = metrics.get("code_smells", "0")
    smells_rating = extract_rating(metrics.get("sqale_rating"))
    save_badge(
        project_key,
        "code_smells",
        make_badge("code smells", smells_count, RATING_COLORS.get(smells_rating, "#555")),
    )

    # Hotspots Reviewed (Count + Rating for color)
    hotspots_count = metrics.get("security_hotspots", "0")
    hotspots_rating = extract_rating(metrics.get("security_review_rating") or metrics.get("security_hotspots_reviewed_rating"))
    save_badge(
        project_key,
        "security_hotspots",
        make_badge("hotspots reviewed", hotspots_count, RATING_COLORS.get(hotspots_rating, "#555")),
    )

    # Duplications (value)
    dups = metrics.get("duplicated_lines_density", "0")
    save_badge(
        project_key,
        "duplicated_lines_density",
        make_badge("duplications", f"{dups}%", color_for_duplications(dups)),
    )



if __name__ == "__main__":
    main()
