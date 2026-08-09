# SonarQube Badge Generator

This repository provides a lightweight, centralized badge generator for projects analyzed with a self‑hosted SonarQube Community Edition instance. Since the Community Edition does not include built‑in badges, this repository acts as a standalone service that produces consistent SVG badges for any project in the organization.

# Purpose

The goal of this repository is to offer a single, reusable location for generating SonarQube badges. Individual project repositories do not need to implement their own badge logic. Instead, they trigger this repository after completing their CI pipeline and SonarQube analysis.

# How It Works
- A project runs its CI pipeline, including a SonarQube scan.
- After the scan finishes, the project triggers a workflow in this repository using workflow_dispatch.
- The workflow retrieves the latest metrics from SonarQube via its REST API.
- The repository generates SVG badges for metrics such as:
    - Coverage
    - Quality Gate Status
    - Bugs
    - Vulnerabilities
    - Code Smells

Generated badges are stored in a dedicated folder per project and can be referenced directly from READMEs or dashboards.

# Repository Structure
- scripts/ — Badge generation logic (e.g., Python or Node.js).
-  badges/ — Output directory containing generated SVG badges, grouped by project.
- .github/workflows/update.yml — Workflow triggered by external pipelines.

# Usage in Project Repositories

After a successful CI pipeline run, a project triggers the badge update workflow:
bash

```sh
curl -X POST \
  -H "Authorization: token $TOKEN" \
  https://api.github.com/repos/<org>/sonar-badges/actions/workflows/update.yml/dispatches \
  -d '{"ref":"main","inputs":{"project":"my-project"}}'
```

Badges can then be embedded in the project’s README:

```md
![Coverage](https://your-host/sonar-badges/my-project/coverage.svg)
![Quality Gate](https://your-host/sonar-badges/my-project/quality_gate.svg)
```

# Benefits

- Centralized badge generation
- Consistent badge design across all projects
- Pipeline‑driven updates
- No polling or cronjobs
- Scalable for any number of repositories

# License

This project is licensed under the MIT License.