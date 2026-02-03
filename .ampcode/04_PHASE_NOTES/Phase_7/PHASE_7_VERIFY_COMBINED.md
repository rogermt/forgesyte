# Phase 7 – Combined Verification Script

This is an **optional alternative** to running individual scripts. It combines all Phase 7 checks into a single TypeScript runner.

## Purpose

Provides a unified entry point for Phase 7 verification with integrated reporting and colored output.

## Usage

```bash
# Run combined verification
ts-node scripts/phase7/verify-combined.ts

# Or as an npm script
npm run verify:phase7

# In GitHub Actions
npm run verify:phase7 -- --ci
```

## Script (TypeScript)

```typescript
#!/usr/bin/env ts-node

/**
 * Phase 7 Combined Verification Script
 *
 * Orchestrates all Phase 7 guardrails in one TypeScript runner.
 * Provides integrated error handling and colored output.
 */

import { execSync } from "child_process";
import * as path from "path";

interface CheckResult {
  name: string;
  passed: boolean;
  output?: string;
  error?: string;
}

class Phase7Verifier {
  private results: CheckResult[] = [];
  private rootDir: string;
  private ciMode: boolean;

  constructor(ciMode = false) {
    this.rootDir = this.getRepoRoot();
    this.ciMode = ciMode;
  }

  private getRepoRoot(): string {
    try {
      return execSync("git rev-parse --show-toplevel", {
        encoding: "utf-8",
      }).trim();
    } catch {
      return process.cwd();
    }
  }

  private log(message: string, color?: string) {
    if (this.ciMode) {
      console.log(message);
    } else if (color) {
      console.log(`\x1b[${color}m${message}\x1b[0m`);
    } else {
      console.log(message);
    }
  }

  private runCheck(
    name: string,
    command: string,
    validator?: (output: string) => boolean
  ) {
    this.log(`\n→ ${name}`, "34");

    try {
      const output = execSync(command, {
        encoding: "utf-8",
        cwd: this.rootDir,
        stdio: ["pipe", "pipe", "pipe"],
      });

      const passed = validator ? validator(output) : true;

      if (passed) {
        this.log("✔ Passed", "32");
        this.results.push({ name, passed: true, output });
      } else {
        this.log("✗ Failed (validation)", "31");
        this.results.push({
          name,
          passed: false,
          output,
          error: "Validation failed",
        });
      }
    } catch (err: any) {
      this.log("✗ Failed", "31");
      const error = err.message || String(err);
      this.results.push({
        name,
        passed: false,
        error,
        output: err.stdout?.toString(),
      });
    }
  }

  run() {
    this.log("\n=== Phase 7 Combined Verification ===\n", "36");

    // Check 1: Forbidden files
    this.runCheck(
      "Forbidden File Check",
      `ts-node ${path.join(this.rootDir, "scripts/phase7/forbidden-file-check.ts")}`
    );

    // Check 2: Skipped tests
    this.runCheck(
      "Skipped Tests Check",
      `ts-node ${path.join(this.rootDir, "scripts/phase7/skipped-tests-check.ts")}`
    );

    // Check 3: Tests
    this.runCheck(
      "Tests (8/8 expected)",
      "cd web-ui && npm test -- --run",
      (output) => output.includes("Tests  8 passed") || output.includes("8 passed")
    );

    // Check 4: Lint
    this.runCheck("Linting", "cd web-ui && npm run lint");

    // Check 5: Type check
    this.runCheck("Type Check", "cd web-ui && npm run type-check");

    // Check 6: Pre-commit
    this.runCheck("Pre-commit Hooks", "uv run pre-commit run --all-files");

    // Summary
    this.printSummary();
  }

  private printSummary() {
    this.log("\n=== Verification Summary ===", "36");

    const passed = this.results.filter((r) => r.passed).length;
    const total = this.results.length;

    this.results.forEach((result) => {
      const icon = result.passed ? "✔" : "✗";
      const color = result.passed ? "32" : "31";
      this.log(`${icon} ${result.name}`, color);
    });

    this.log(`\n${passed}/${total} checks passed\n`, passed === total ? "32" : "31");

    if (passed === total) {
      this.log(
        "✔ Phase 7 verification complete. PR is ready for submission.",
        "32"
      );
      process.exit(0);
    } else {
      this.log(
        "✗ Phase 7 verification failed. Fix issues above.",
        "31"
      );
      this.printFailures();
      process.exit(1);
    }
  }

  private printFailures() {
    const failures = this.results.filter((r) => !r.passed);
    if (failures.length === 0) return;

    this.log("\n=== Failures ===", "31");
    failures.forEach((result) => {
      this.log(`\n${result.name}:`, "31");
      if (result.error) {
        this.log(`  Error: ${result.error}`, "31");
      }
      if (result.output) {
        this.log(`  Output:\n${result.output}`, "33");
      }
    });
  }
}

// Main
const args = process.argv.slice(2);
const ciMode = args.includes("--ci");
const verifier = new Phase7Verifier(ciMode);

verifier.run();
```

## How to Integrate

### Option 1: As a Standalone Script

Save to: `scripts/phase7/verify-combined.ts`

Run manually:

```bash
ts-node scripts/phase7/verify-combined.ts
```

### Option 2: Add to package.json

```json
{
  "scripts": {
    "verify:phase7": "ts-node scripts/phase7/verify-combined.ts",
    "verify:phase7:ci": "ts-node scripts/phase7/verify-combined.ts --ci"
  }
}
```

### Option 3: GitHub Actions

Add to `.github/workflows/pr-checks.yml`:

```yaml
- name: Phase 7 – Verify PR
  if: contains(github.head_ref, 'phase7')
  run: npm run verify:phase7:ci
```

## Features

- **Unified runner** – All checks in one command
- **Colored output** – Easy to scan results (unless `--ci` mode)
- **Error handling** – Graceful handling of failures
- **CI-friendly** – `--ci` flag disables colors for GitHub Actions
- **Integrated validation** – Custom validators (e.g., test count)
- **Clear reporting** – Summary with pass/fail counts

## Exit Codes

- `0` – All checks passed
- `1` – One or more checks failed

## Typical Output (Success)

```
=== Phase 7 Combined Verification ===

→ Forbidden File Check
✔ Passed

→ Skipped Tests Check
✔ Passed

→ Tests (8/8 expected)
✔ Passed

→ Linting
✔ Passed

→ Type Check
✔ Passed

→ Pre-commit Hooks
✔ Passed

=== Verification Summary ===
✔ Forbidden File Check
✔ Skipped Tests Check
✔ Tests (8/8 expected)
✔ Linting
✔ Type Check
✔ Pre-commit Hooks

6/6 checks passed

✔ Phase 7 verification complete. PR is ready for submission.
```

## Notes

- This script is **optional** – the individual scripts work independently
- Useful if you prefer a single command to all checks
- CI mode (`--ci`) suppresses colored output for GitHub Actions
- Takes ~30 seconds to complete (mostly tests)
- Good alternative to shell script if you prefer TypeScript
