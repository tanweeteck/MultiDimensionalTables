# Table: Releases

Lightweight log of shipped versions. Auto-created by automation A9 when a Milestone is released.

## Fields

| Field | Type | Required | Notes |
|---|---|---|---|
| Version | Text | ✓ | e.g. `v0.4.0` |
| Tag Date | Date | ✓ | Date of the git tag / GitHub release |
| Linked Milestone | Link → Milestones |   | One-to-one with the released milestone |
| Highlights | Long text |   | DCO writes the marketing summary here |
| Breaking Changes | Long text |   | If any |
| Linked Features | Rollup |   | from Linked Milestone → Features |
| GitHub Release URL | URL |   | |
| Announcement Posted | Checkbox |   | DCO checks after posting changelog |

## Notes

- This table is intentionally thin — release notes live in GitHub Releases. The row is for cross-team visibility and the dashboard's "last shipped" widget.
