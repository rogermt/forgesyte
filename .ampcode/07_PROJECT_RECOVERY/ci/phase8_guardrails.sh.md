#Create this scripts/phase8_guardrails.sh
#!/usr/bin/env bash
set -e

echo "Running Phase 8 Guardrails..."

ERROR=0

# 1. Structured logging check
if grep -R "print(" -n server/ plugins/; then
  echo "::error::Found raw print() statements. Structured logging required."
  ERROR=1
fi

# 2. Normalisation enforcement
if ! grep -R "normalize_" -n server/ plugins/; then
  echo "::error::No normalization functions detected. Phase 8 requires canonical normalization."
  ERROR=1
fi

# 3. Manifest validity
if ! grep -R "manifest" -n server/; then
  echo "::error::Manifest validation missing."
  ERROR=1
fi

# 4. Job lifecycle invariants
if grep -R "/run" -n server/; then
  echo "::error::Legacy /run endpoint detected. Must not exist in Phase 8."
  ERROR=1
fi

# 5. Plugin loader guardrail
if ! grep -R "load_plugins" -n server/; then
  echo "::error::Plugin loader not invoked."
  ERROR=1
fi

if [ "$ERROR" -eq 1 ]; then
  exit 1
fi

echo "Phase 8 Guardrails Passed."
