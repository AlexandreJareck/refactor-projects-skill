---
name: refactor-arch
description: Analyze and audit a backend project, then refactor confirmed findings into an MVC architecture while preserving its HTTP behavior. Use for an explicit architecture audit and refactoring request, including Flask or Express projects.
---

# Refactor architecture

Operate on the current project directory. Keep the three phases visible in the conversation and finish each phase before starting the next. Inspect real code; do not infer a finding from a filename or a pattern match alone. Treat report paths supplied by the caller as output paths outside the target project when requested.

## Phase 1 — Project analysis

Read [project-analysis.md](references/project-analysis.md). Identify language, framework and installed or declared versions, dependencies, database, application domain, architecture, entry point and HTTP endpoints. Count source files actually inspected, excluding dependencies, generated files, tests and skill files; state the counting rule. Print a compact analysis summary. Capture a reproducible baseline of existing endpoint behavior using isolated test data when feasible.

## Phase 2 — Architecture audit

Read [anti-patterns.md](references/anti-patterns.md) and [audit-report.md](references/audit-report.md). Inspect the complete relevant codebase and compare each plausible issue with its detection signals. For every real finding, cite the exact original file and line or shortest meaningful line range, explain evidence, impact and a concrete recommendation. Apply the severity definitions in the catalog; order findings CRITICAL, HIGH, MEDIUM, LOW. Check for deprecated APIs against the project's installed version and authoritative documentation; say "none verified" when appropriate. Print the full report and summarize counts. **Stop here and ask the user for explicit confirmation before writing or changing any file, including the report, and before Phase 3.** The original invocation is not confirmation. If confirmation is denied, stop without file changes.

## Phase 3 — Confirmed refactoring and validation

Only after confirmation, save the unchanged Phase 2 report to the caller's requested path, preserving its pre-refactor line references. Read [mvc-guidelines.md](references/mvc-guidelines.md) and [refactoring-playbook.md](references/refactoring-playbook.md). Plan the smallest stack-appropriate MVC separation that addresses the confirmed findings. Implement the changes; preserve existing routes and response contracts when compatible with correcting a demonstrated security flaw. Explain intentional contract changes. Keep configuration out of code and errors handled centrally. Validate that the application boots and every original endpoint still responds in both representative success and failure cases, using isolated data. Compare to the baseline, run available tests and relevant new behavior tests, then report results and remaining risks. Never claim an issue is gone or a test passed without evidence.
