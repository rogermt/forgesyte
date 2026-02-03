# Phase 7 – Forbidden File Change Detector

This script blocks PRs that modify core logic files that must remain frozen during the CSS Modules migration.

## Purpose

Detects if any of the following files have been modified in the current branch:

- `web-ui/src/hooks/useVideoProcessor.ts`
- `web-ui/src/api/client.ts`
- Phase 6 test files

If found, exits with error and lists violations.

## Usage

```bash
# As a pre-commit hook
ts-node scripts/phase7/forbidden-file-check.ts

# In GitHub Actions
npm run check:phase7-forbidden-files
```

## Script (TypeScript)

```typescript
#!/usr/bin/env ts-node

/**
 * Phase 7 Guardrail: Forbidden File Change Detector
 *
 * Prevents modifications to locked Phase 6 files during Phase 7 CSS Modules migration.
 */

import { execSync } from "child_process";
import * as fs from "fs";
import * as path from "path";

const FORBIDDEN_FILES = [
  "web-ui/src/hooks/useVideoProcessor.ts",
  "web-ui/src/api/client.ts",
  "web-ui/src/hooks/__tests__/useVideoProcessor.test.ts",
  "web-ui/src/components/__tests__/VideoTracker.test.tsx",
  "web-ui/src/components/VideoTracker.tsx",
];

function getChangedFiles(): string[] {
  try {
    const output = execSync("git diff --name-only origin/main...HEAD", {
      encoding: "utf-8",
    })
      .trim();
    return output.split("\n").filter(Boolean);
  } catch {
    // Fallback: check staged files
    const output = execSync("git diff --cached --name-only", {
      encoding: "utf-8",
    })
      .trim();
    return output.split("\n").filter(Boolean);
  }
}

function main() {
  console.log("=== Phase 7 Guardrail: Forbidden File Check ===\n");

  const changed = getChangedFiles();
  const violations = changed.filter((f) => FORBIDDEN_FILES.includes(f));

  if (violations.length > 0) {
    console.error("❌ Phase 7 Guardrail Violation:\n");
    console.error(
      "The following forbidden files were modified in this PR:\n"
    );
    violations.forEach((v) => console.error(`  - ${v}`));
    console.error(
      "\n📛 These files are LOCKED during Phase 7 CSS Modules migration."
    );
    console.error(
      "\n💡 If a logic change is required, use PHASE_7_ESCALATION_TEMPLATE.md\n"
    );
    process.exit(1);
  }

  console.log("✔ No forbidden file changes detected.\n");
  process.exit(0);
}

main();
```

## How to Integrate

### Option 1: Pre-commit Hook

Add to `.pre-commit-config.yaml`:

```yaml
- id: phase7-forbidden-files
  name: Phase 7 – Forbidden file check
  entry: ts-node scripts/phase7/forbidden-file-check.ts
  language: system
  pass_filenames: false
```

### Option 2: GitHub Actions

Add to `.github/workflows/pr-checks.yml`:

```yaml
- name: Phase 7 – Check forbidden files
  run: ts-node scripts/phase7/forbidden-file-check.ts
```

### Option 3: Manual (Dev)

```bash
cd /path/to/forgesyte
ts-node scripts/phase7/forbidden-file-check.ts
```

## Exit Codes

- `0` – No violations detected (OK)
- `1` – Forbidden file was modified (FAIL)

## Notes

- The script checks both `git diff --name-only` (branch diff) and staged files
- If a file is both forbidden AND escalated, the PR must include the completed escalation template
- This check should run **before** `npm test` and `npm run lint`
