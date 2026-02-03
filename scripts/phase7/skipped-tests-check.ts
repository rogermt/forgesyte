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
