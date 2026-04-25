---
name: Bug report
about: Report a defect so it lands in the Bugs table
title: "[Bug] "
labels: ["bug", "severity:s2"]
assignees: []
---

## Summary
<!-- One-sentence description of the bug. -->

## Affected version
<!-- e.g. v0.3.1 -->

## Repro steps
1.
2.
3.

## Expected
<!-- What should happen. -->

## Actual
<!-- What happened. -->

## Reproducibility
- [ ] Always
- [ ] Sometimes
- [ ] Once

## Severity hint (optional)

Replace the default `severity:s2` label with one of:

- `severity:s0` — production down, data loss, security
- `severity:s1` — major feature broken, no workaround
- `severity:s2` — degraded, workaround exists *(default)*
- `severity:s3` — cosmetic / edge

> The Bitable sync routes this issue into the **Bugs** table and reads `severity:*` to set the Severity field.
