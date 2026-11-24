# Security Scan Report

> **GATE STATUS: FAILED** — Blocking findings require remediation before release.

**Project:** brownfield  
**Scan Time:** 2026-11-24T13:13:17.297067+00:00  
**Gate Result:** FAILED (scan_incomplete)

## Risk Overview



| Metric | Count |
|--------|------:|
| **[CRIT]** | 0 |
| **[HIGH]** | 0 |
| **[MED]** | 0 |
| **[LOW]** | 0 |
| **Total** | **0** |
| Suppressed | 0 |
| Errors | 1 |

## Detailed Reports

| Scan Type | Status | Findings | Report |
|-----------|--------|----------|--------|

## Tools

| Tool | Available | Version |
|------|-----------|---------|
| semgrep | — |  |
| trivy | — |  |
| gitleaks | Yes | 8.30.1 |
| codeql | — |  |
| syft | — |  |
| grype | — |  |
| nuclei | — |  |
| cosign | — |  |

## Errors

- **system** (no_tools_available): No scanning tools available for requested types: sast, secrets, deps, licenses, iac. Missing: semgrep, trivy
