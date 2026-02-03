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
