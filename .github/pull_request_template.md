# Phase 11 PR Checklist

## Required (Authoritative)

- [ ] All server tests pass locally (`cd server && uv run pytest`)
- [ ] No Phase 9 or Phase 10 invariants broken
- [ ] No API contract changes unless explicitly approved via RFC
- [ ] No plugin can crash the server
- [ ] If test files changed: commit message includes `TEST-CHANGE:` with justification

## Required (CI)

- [ ] CI server tests passed
- [ ] CI web-ui tests passed (Playwright)
- [ ] CI contract tests passed

## Optional (Code Quality)

- [ ] Code follows PEP 8 style guide
- [ ] Type hints added to new functions
- [ ] Docstrings updated or added
- [ ] No debugging print statements left in code

## Optional (Documentation)

- [ ] README updated (if user-facing)
- [ ] Architecture doc updated (if design changed)
- [ ] API endpoint documented (if new endpoint)
- [ ] Plugin contract updated (if plugin API changed)

## Description

Describe your changes clearly. Include:

- **What** you changed
- **Why** you changed it
- **How** you tested it
- **Related issues** (e.g., "Closes #123")

## Related Issues

Closes #[issue-number]

## Notes

Any special considerations, gotchas, or follow-up work?
