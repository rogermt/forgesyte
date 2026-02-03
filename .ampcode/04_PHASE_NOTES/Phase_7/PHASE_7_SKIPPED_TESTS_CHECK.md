# Phase 7 – Skipped Tests Detector

This script blocks PRs containing skipped or isolated tests.

## Purpose

Detects patterns indicating skipped/isolated tests:

- `it.skip`
- `describe.skip`
- `test.skip`
- `xit(`
- `xdescribe(`
- `xtest(`
- `.only(`

If found, exits with error and lists occurrences.

## Usage

```bash
# As a pre-commit hook
ts-node scripts/phase7/skipped-tests-check.ts

# In GitHub Actions
npm run check:phase7-skipped-tests
```

## Script (TypeScript)

```typescript
#!/usr/bin/env ts-node

/**
 * Phase 7 Guardrail: Skipped Tests Detector
 *
 * Prevents isolated or skipped tests from being committed during Phase 7.
 */

import { execSync } from "child_process";

const SKIP_PATTERNS = [
  "it.skip",
  "describe.skip",
  "test.skip",
  "xit(",
  "xdescribe(",
  "xtest(",
  ".only(",
];

interface ViolationMatch {
  file: string;
  line: number;
  content: string;
}

function searchForSkippedTests(): ViolationMatch[] {
  const violations: ViolationMatch[] = [];

  SKIP_PATTERNS.forEach((pattern) => {
    try {
      const output = execSync(
        `git grep -n "${pattern}" -- web-ui/src ":(exclude)node_modules"`,
        { encoding: "utf-8" }
      )
        .trim();

      if (!output) return;

      const matches = output.split("\n");
      matches.forEach((match) => {
        const [fileLine, ...contentParts] = match.split(":");
        const [file, lineStr] = fileLine.split(":");
        const line = parseInt(lineStr, 10);
        const content = contentParts.join(":").trim();

        // Skip if line contains "// APPROVED:" comment
        if (!content.includes("// APPROVED:")) {
          violations.push({ file, line, content });
        }
      });
    } catch {
      // Pattern not found in any files
    }
  });

  return violations;
}

function main() {
  console.log("=== Phase 7 Guardrail: Skipped Tests Check ===\n");

  const violations = searchForSkippedTests();

  if (violations.length > 0) {
    console.error("❌ Skipped or isolated tests detected:\n");
    violations.forEach((v) => {
      console.error(`  ${v.file}:${v.line}`);
      console.error(`    ${v.content}\n`);
    });
    console.error(
      "📛 Skipped tests are forbidden during Phase 7 CSS Modules migration.\n"
    );
    console.error("💡 Options:");
    console.error("  1. Remove the .skip / .only");
    console.error("  2. Add '// APPROVED: <reason>' to the same line");
    console.error("  3. Use PHASE_7_ESCALATION_TEMPLATE.md\n");
    process.exit(1);
  }

  console.log("✔ No skipped tests found.\n");
  process.exit(0);
}

main();
```

## How to Integrate

### Option 1: Pre-commit Hook

Add to `.pre-commit-config.yaml`:

```yaml
- id: phase7-skipped-tests
  name: Phase 7 – Skipped tests check
  entry: ts-node scripts/phase7/skipped-tests-check.ts
  language: system
  pass_filenames: false
```

### Option 2: GitHub Actions

Add to `.github/workflows/pr-checks.yml`:

```yaml
- name: Phase 7 – Check skipped tests
  run: ts-node scripts/phase7/skipped-tests-check.ts
```

### Option 3: Manual (Dev)

```bash
cd /path/to/forgesyte
ts-node scripts/phase7/skipped-tests-check.ts
```

## Exemption Pattern

If a skipped test is temporarily necessary during Phase 7, add an approval comment:

```typescript
it.skip("test name", () => {
  // APPROVED: Temporary skip for refactoring - will re-enable in Phase 8
  // ...
});
```

The check will allow this line through.

## Exit Codes

- `0` – No violations detected (OK)
- `1` – Skipped tests found (FAIL)

## Notes

- Scans only `web-ui/src/` to avoid false positives in node_modules
- The `// APPROVED:` pattern must be on the same line as the skip
- This check should run **early** in the PR validation pipeline
- Violations should be reviewed before approval
