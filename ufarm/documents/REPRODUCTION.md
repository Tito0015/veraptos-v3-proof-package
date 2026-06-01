# UFarm Local Fracture — Empirical Audit Reproduction

Reproduces the three audit points for Veraptos V3.0 optimization (sigmoid relaxation, gradient convergence, 2^64 / profit ground truth).

## Prerequisites

- Foundry (`forge`)
- Python 3.12+ with PyTorch (use `.venv-ste` in this directory)

## Quick run (from repo root)

```bash
bash scripts/run_empirical_audit.sh
```

Logs land in `artifacts/empirical_audit/`.

## Manual steps

### 1. Foundry — `testLocalFracture`

```bash
cd local_sandbox_gist
forge test --match-test testLocalFracture -vvvv
forge test --match-test test2Power64Boundary -vv
```

Expected: `PROFIT EXTRACTED: 2500000000000000500 wei`, `assertGt(profit, 0)` PASS.

### 2. PyTorch — gradient + STE + sigmoid

```bash
cd local_sandbox_gist
source .venv-ste/bin/activate   # if present
python test_ufarm_gradient_convergence.py
```

### 3. Production code references

| Claim | File | Lines |
|-------|------|-------|
| Sigmoid relaxation | `services/swarm-director/agents/jepa_evm/nodes.py` | ~951-957 |
| BPTT loop | same | ~939-978 |
| STE vault desync | same | ~658-663 |

### 4. 2^64 in UFarm Halmos bytecode

```bash
python3 -c "
import json
from pathlib import Path
p = Path('targets/web3/ufarm/out/UFarmSignalLagHalmos.t.sol/UFarmSignalLagHalmosTest.json')
bc = json.loads(p.read_text())['bytecode']['object']
assert '10000000000000000' in bc
print('2^64 hex present in bytecode')
"
```

Run from repository root.

## Formal proof document

See `/opt/hybrid-soc/VERAPTOS_EMPIRICAL_AUDIT_PROOF.md`.
