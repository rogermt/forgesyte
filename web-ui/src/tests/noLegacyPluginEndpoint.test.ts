/**
 * TEST-CHANGE (Phase 11): Web-UI must never call /v1/plugins/{name}
 *
 * Governance test to ensure web-ui only uses canonical endpoint:
 * /v1/plugins/{name}/health
 *
 * This prevents accidental drift to legacy endpoints and ensures
 * Phase 11 API contract compliance.
 */

import fs from "fs";
import path from "path";
import { describe, it, expect } from "vitest";

const SRC_DIR = path.join(__dirname, "..", "src");

function scan(dir: string, out: string[] = []): string[] {
  try {
    for (const f of fs.readdirSync(dir)) {
      const full = path.join(dir, f);
      const stat = fs.statSync(full);
      if (stat.isDirectory()) {
        // Skip node_modules and build directories
        if (!["node_modules", "dist", "build", ".next"].includes(f)) {
          scan(full, out);
        }
      } else if (f.endsWith(".ts") || f.endsWith(".tsx")) {
        out.push(full);
      }
    }
  } catch {
    // Skip inaccessible directories
  }
  return out;
}

describe("Phase 11 API Contract - Web-UI Compliance", () => {
  it("web-ui never calls legacy /v1/plugins/{name}", () => {
    const files = scan(SRC_DIR);
    const forbidden: { file: string; match: string }[] = [];

    for (const file of files) {
      try {
        const content = fs.readFileSync(file, "utf8");

        // Check for legacy endpoint patterns
        const patterns = [
          // Pattern 1: Template literal like /v1/plugins/${name}
          /\/v1\/plugins\/\$\{[^}]+\}(?!\/health)/,
          // Pattern 2: String concatenation like /v1/plugins/" + name
          /\/v1\/plugins\/["']\s*\+/,
          // Pattern 3: Direct plugin name pattern (but not /health)
          /\/v1\/plugins\/[a-zA-Z0-9_-]+(?!\/health)/,
        ];

        for (const pattern of patterns) {
          const match = content.match(pattern);
          if (match) {
            forbidden.push({
              file,
              match: match[0],
            });
          }
        }
      } catch {
        // Skip unreadable files
      }
    }

    expect(forbidden).toHaveLength(0);
    if (forbidden.length > 0) {
      const details = forbidden
        .map(({ file, match }) => `${file}: "${match}"`)
        .join("\n");
      throw new Error(
        `Phase 11 violation: Web-UI calls legacy /v1/plugins/{name} endpoint.\n${details}\n` +
          `Use /v1/plugins/{name}/health instead.`
      );
    }
  });
});
