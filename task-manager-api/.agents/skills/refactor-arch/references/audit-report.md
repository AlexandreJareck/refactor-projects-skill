# Audit report template

Print this report during Phase 2. Do not save it until the user confirms Phase 3. Keep the printed text available verbatim for later persistence, with pre-refactor locations. **Use the headings and field labels below exactly; do not merge the finding fields into prose paragraphs.** The project analysis can precede the report as live output, but the saved audit must contain every section shown here.

```markdown
# Architecture audit — <project>

## Project analysis
- Language and framework: <version and source>
- Database and domain: <facts>
- Architecture and entry point: <facts>
- Source files analyzed: <count and counting rule>
- Original endpoints: <method/path inventory or link to inventory>

## Summary
CRITICAL: <n> | HIGH: <n> | MEDIUM: <n> | LOW: <n> | Total: <n>
Deprecated APIs: <verified finding IDs or "none verified">

## Findings
### <ID> [CRITICAL|HIGH|MEDIUM|LOW] <short title>
- File: `<relative/path>:<exact-line-or-small-range>`
- Evidence: <what the code does, without leaking actual secrets>
- Impact: <specific failure or risk>
- Recommendation: <concrete change>
- Manual-analysis match: <ID or "additional finding" when caller supplied a baseline>

## Proposed MVC change
<short, stack-appropriate change outline>

## Confirmation gate
Phase 2 complete. Confirm Phase 3 before any file is written or changed.
```

Order findings by severity, then by path and line for stable output. Count each distinct root problem once; related locations can be cited together. Record uncertainty when impact requires runtime verification. If the caller requires minimum counts, verify real findings meet them; do not fabricate entries. Stop at the confirmation gate.
