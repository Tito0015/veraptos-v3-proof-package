#!/usr/bin/env bash
# Veraptos V3.0 empirical audit — reproducible execution proof
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
GIST="${ROOT}/local_sandbox_gist"
ARTIFACTS="${ROOT}/local_sandbox_gist/audit_logs"
mkdir -p "${ARTIFACTS}" 2>/dev/null || ARTIFACTS="/tmp/veraptos_empirical_audit_$$"
mkdir -p "${ARTIFACTS}"

echo "=== Veraptos Empirical Audit ==="
echo "Root: ${ROOT}"

echo ""
echo "[1/3] Pytest (empirical audit integration)..."
cd "${ROOT}"
python3 -m pytest tests/test_ufarm_empirical_audit.py -v --tb=short 2>&1 | tee "${ARTIFACTS}/pytest.log"

echo ""
echo "[2/3] Foundry testLocalFracture..."
if command -v forge >/dev/null 2>&1; then
  cd "${GIST}"
  forge test --match-test testLocalFracture -vvvv 2>&1 | tee "${ARTIFACTS}/forge_testLocalFracture.log"
  forge test --match-test test2Power64Boundary -vv 2>&1 | tee "${ARTIFACTS}/forge_test2Power64.log"
else
  echo "SKIP: forge not installed" | tee "${ARTIFACTS}/forge_testLocalFracture.log"
fi

echo ""
echo "[3/3] PyTorch gradient convergence..."
if [[ -x "${GIST}/.venv-ste/bin/python" ]]; then
  "${GIST}/.venv-ste/bin/python" "${GIST}/test_ufarm_gradient_convergence.py" 2>&1 | tee "${ARTIFACTS}/gradient_convergence.log"
elif python3 -c "import torch" 2>/dev/null; then
  python3 "${GIST}/test_ufarm_gradient_convergence.py" 2>&1 | tee "${ARTIFACTS}/gradient_convergence.log"
else
  echo "SKIP: torch not available" | tee "${ARTIFACTS}/gradient_convergence.log"
fi

echo ""
echo "Artifacts written to: ${ARTIFACTS}"
echo "Proof document: ${ROOT}/VERAPTOS_EMPIRICAL_AUDIT_PROOF.md"
