#!/usr/bin/env python3
"""
Phase 11 Plugin Audit Script

Scans the plugin health API and validates:
- All plugins have valid states
- No unexpected drift
- Registry matches Health API
- GPU/model dependencies satisfied
- No critical issues

Usage:
    python scripts/audit_plugins.py
    python scripts/audit_plugins.py --url http://custom-server:8000
    python scripts/audit_plugins.py --json > audit-report.json
"""

import sys
import json
import argparse
from datetime import datetime
from typing import Optional

try:
    import requests
except ImportError:
    print("ERROR: requests library not installed")
    print("Install with: pip install requests")
    sys.exit(1)


class PluginAudit:
    """Audit plugin health and governance."""

    VALID_STATES = {"LOADED", "INITIALIZED", "RUNNING", "FAILED", "UNAVAILABLE"}
    AVAILABLE_STATES = {"LOADED", "INITIALIZED", "RUNNING"}
    ERROR_STATES = {"FAILED", "UNAVAILABLE"}

    def __init__(self, api_url: str = "http://localhost:8000/v1/plugins"):
        self.api_url = api_url
        self.base_url = api_url.rsplit("/v1", 1)[0]
        self.plugins = []
        self.errors = []
        self.warnings = []

    def run(self) -> int:
        """Run full audit. Returns 0 if healthy, 1 if issues found."""
        print("Phase 11 Plugin Audit")
        print("=" * 60)

        # 1. Connect
        if not self._connect():
            return 1

        # 2. Fetch plugins
        if not self._fetch_plugins():
            return 1

        # 3. Validate each plugin
        self._validate_plugins()

        # 4. Check consistency
        self._check_consistency()

        # 5. Report
        return self._report()

    def _connect(self) -> bool:
        """Verify API is reachable."""
        print(f"\n[1/5] Connecting to API: {self.api_url}")
        try:
            resp = requests.get(self.api_url, timeout=5)
            resp.raise_for_status()
            print("✓ API is reachable")
            return True
        except requests.exceptions.ConnectionError:
            self.errors.append(
                f"Cannot connect to API at {self.api_url}\n"
                "  Is the server running?\n"
                f"  Try: curl {self.api_url}"
            )
            return False
        except requests.exceptions.Timeout:
            self.errors.append(f"API timeout at {self.api_url}")
            return False
        except Exception as exc:
            self.errors.append(f"API error: {exc}")
            return False

    def _fetch_plugins(self) -> bool:
        """Fetch list of all plugins."""
        print("\n[2/5] Fetching plugins...")
        try:
            resp = requests.get(self.api_url, timeout=5)
            resp.raise_for_status()
            
            data = resp.json()
            
            # Handle both list and dict responses
            if isinstance(data, dict):
                self.plugins = data.get("plugins", [])
                total = data.get("total", len(self.plugins))
            else:
                self.plugins = data
                total = len(self.plugins)
            
            print(f"✓ Found {total} plugin(s)")
            if not self.plugins:
                self.warnings.append("No plugins loaded")
                return True
            
            return True
        except Exception as exc:
            self.errors.append(f"Failed to fetch plugins: {exc}")
            return False

    def _validate_plugins(self):
        """Validate each plugin individually."""
        print(f"\n[3/5] Validating {len(self.plugins)} plugin(s)...")
        
        for plugin in self.plugins:
            name = plugin.get("name", "UNKNOWN")
            state = plugin.get("state", "UNKNOWN")
            
            # Validate state
            if state not in self.VALID_STATES:
                self.errors.append(
                    f"Plugin '{name}': invalid state '{state}'"
                )
            
            # Check detail health
            self._validate_plugin_detail(name, state)
            
            # Check for issues
            if state == "FAILED":
                reason = plugin.get("reason")
                print(f"  ⚠ {name}: FAILED ({reason})")
            elif state == "UNAVAILABLE":
                reason = plugin.get("reason")
                print(f"  ⊘ {name}: UNAVAILABLE ({reason})")
            elif state in self.AVAILABLE_STATES:
                print(f"  ✓ {name}: {state}")

    def _validate_plugin_detail(self, name: str, list_state: str):
        """Fetch and validate plugin health detail."""
        try:
            resp = requests.get(f"{self.api_url}/{name}/health", timeout=5)
            
            if resp.status_code == 404:
                self.warnings.append(
                    f"Plugin '{name}' in list but not in detail API"
                )
                return
            
            if resp.status_code != 200:
                self.errors.append(
                    f"Plugin '{name}' health returned {resp.status_code}"
                )
                return
            
            detail = resp.json()
            detail_state = detail.get("state")
            
            # Check consistency
            if detail_state != list_state:
                self.errors.append(
                    f"Plugin '{name}' state mismatch: "
                    f"list={list_state}, detail={detail_state}"
                )
            
            # Check required fields
            if not detail.get("name"):
                self.errors.append(f"Plugin '{name}' missing 'name' field")
            
            if "state" not in detail:
                self.errors.append(f"Plugin '{name}' missing 'state' field")
            
            # Check metrics
            if "success_count" not in detail:
                self.warnings.append(f"Plugin '{name}' missing success_count")
            
            if "error_count" not in detail:
                self.warnings.append(f"Plugin '{name}' missing error_count")
        
        except Exception as exc:
            self.errors.append(f"Plugin '{name}' detail fetch failed: {exc}")

    def _check_consistency(self):
        """Check overall system consistency."""
        print("\n[4/5] Checking consistency...")
        
        # Count states
        available = sum(1 for p in self.plugins if p.get("state") in self.AVAILABLE_STATES)
        failed = sum(1 for p in self.plugins if p.get("state") == "FAILED")
        unavailable = sum(1 for p in self.plugins if p.get("state") == "UNAVAILABLE")
        
        # Report
        print(f"  Available: {available}")
        print(f"  Failed: {failed}")
        print(f"  Unavailable: {unavailable}")
        
        if failed > 0:
            self.warnings.append(f"{failed} plugin(s) in FAILED state")
        
        if unavailable > 0:
            self.warnings.append(f"{unavailable} plugin(s) UNAVAILABLE (missing deps/GPU)")

    def _report(self) -> int:
        """Print final report. Returns exit code."""
        print("\n[5/5] Final Report")
        print("=" * 60)
        
        if self.errors:
            print(f"\n❌ ERRORS ({len(self.errors)}):")
            for i, error in enumerate(self.errors, 1):
                print(f"  {i}. {error}")
        
        if self.warnings:
            print(f"\n⚠️  WARNINGS ({len(self.warnings)}):")
            for i, warning in enumerate(self.warnings, 1):
                print(f"  {i}. {warning}")
        
        if not self.errors and not self.warnings:
            print("\n✅ All checks passed")
            print(f"   {len(self.plugins)} plugin(s) healthy")
            return 0
        
        if self.errors:
            print(f"\n❌ Audit FAILED ({len(self.errors)} error(s))")
            return 1
        
        print(f"\n⚠️  Audit completed with warnings ({len(self.warnings)})")
        return 0

    def to_json(self) -> str:
        """Return audit results as JSON."""
        return json.dumps({
            "timestamp": datetime.utcnow().isoformat(),
            "api_url": self.api_url,
            "plugins_count": len(self.plugins),
            "plugins": self.plugins,
            "errors": self.errors,
            "warnings": self.warnings,
            "status": "PASSED" if not self.errors else "FAILED",
        }, indent=2)


def main():
    """Command-line interface."""
    parser = argparse.ArgumentParser(
        description="Audit Phase 11 plugin health"
    )
    parser.add_argument(
        "--url",
        default="http://localhost:8000/v1/plugins",
        help="Plugin health API URL (default: http://localhost:8000/v1/plugins)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON",
    )
    
    args = parser.parse_args()
    
    audit = PluginAudit(api_url=args.url)
    
    if args.json:
        # Run silently
        try:
            requests.get(args.url, timeout=5)
            audit._fetch_plugins()
            audit._validate_plugins()
            audit._check_consistency()
            print(audit.to_json())
        except Exception as exc:
            print(json.dumps({
                "status": "ERROR",
                "error": str(exc),
            }, indent=2))
            return 1
    else:
        # Run with verbose output
        return audit.run()


if __name__ == "__main__":
    sys.exit(main())
