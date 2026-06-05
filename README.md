# Veraptos V3.0 — Evidence Package

**Archive date:** 2026-06-01  
**Campaign scope:** JEPA-EVM neuro-symbolic invariant search against **Damn Vulnerable DeFi (DVD)** calibration targets and **UFarm** arithmetic-friction analysis  
**Operator constraint:** Passive artifact bundle — no hunts, forge runs, or evaluations were executed to produce this package.

---

## System Overview

**Veraptos V3.0 — Dual-Stack Neuro-Symbolic EVM Invariant Solver**

Veraptos combines two execution stacks:

1. **JEPA-EVM (Stack B)** — A six-node LangGraph pipeline that ingests Solidity topology (CFG + Slither features), runs **BPTT with Adam** over schema-defined invariant energies, and emits Foundry validation scaffolds when router energy crosses threshold **0.82**.

2. **Swarm LangGraph (Stack A)** — Full bounty orchestration (OSINT, scanners, HITL stations). JEPA-EVM operates independently via `veraptos jepa`; this package focuses on **empirical JEPA calibration evidence**.

The core graph topology is defined in `architecture/jepa_evm_graph.py`:

```
Perception_Mapper → JEPA_Latent_MPC → Critic_Energy_Gate
  ├─ high_energy_found  → Translator_LLM → HIL_Foundry_Execution → Reality_Backprop
  ├─ low_energy_continue → (loop, max 100 MPC iterations)
  └─ mpc_exhausted       → END
```

**Search mechanism:** Differentiable energy maximization on non-linear invariant expressions (ReLU accounting mismatches, AMM oracle desync, vault STE desync) — not random fuzzing or Slither rule matching alone. Slither JSON augments perception tensors; Foundry tests provide empirical ground truth.

---

## Directory Layout

```
paradigm_gist_package/
├── README.md                          ← this file
├── architecture/
│   ├── jepa_evm_graph.py              ← LangGraph compile + routers
│   └── JEPA_Architecture_Evolution_Report.md
├── ufarm/                             ← UFarm 2^64 wei empirical audit campaign
├── dvd_calibration/                   ← DVD challenge calibrations + scaffolds
├── templates/                         ← Jinja2 PoC generator template
└── integration_tests/                 ← pytest proofs (read-only references)
```

---

## File Manifest

### Architecture

| File | Demonstrates |
|------|--------------|
| `architecture/jepa_evm_graph.py` | Raw six-node JEPA-EVM LangGraph: MPC loop, energy router (`≥ 0.82` → Translator), Foundry HIL path, reality backprop on revert. |
| `architecture/JEPA_Architecture_Evolution_Report.md` | Design evolution from Medusa-centric fuzzing to Class 3 JEPA factory; Hamiltonian energy scoring, block pinning, observable bridge. |
| `templates/base_exploit.t.sol.j2` | Jinja2 template used by `poc_builder.py` / Translator LLM to wrap synthesized test bodies in Foundry harnesses. |

### UFarm Campaign (`ufarm/`)

| File | Demonstrates |
|------|--------------|
| `ufarm/MANIFEST.json` | Campaign index: audit points (sigmoid relaxation, BPTT Adam, 2^64 ground truth), numerical constants, file inventory. |
| `ufarm/documents/VERAPTOS_EMPIRICAL_AUDIT_PROOF.md` | Formal three-point audit: math trace (sigmoid + STE), convergence proof, Foundry ground truth at 2^64 wei boundary. |
| `ufarm/documents/REPRODUCTION.md` | Step-by-step reproduction guide mapping audit claims to source line ranges in `nodes.py`. |
| `ufarm/execution_logs/gradient_convergence.log` | **Adam optimizer telemetry:** 90-epoch PyTorch loop showing amount/profit/gradient columns; final profit **8.048×10¹⁸ wei**; STE and sigmoid relaxation validated. |
| `ufarm/execution_logs/forge_testLocalFracture.log` | Foundry **PASS** on `testLocalFracture()` — profit extracted **2,500,000,000,000,000,500 wei** at 2^64 coordinate. |
| `ufarm/execution_logs/forge_test2Power64.log` | Foundry validation of exact **2^64 wei** (`18446744073709551616`) deposit boundary. |
| `ufarm/execution_logs/forge_LocalVaultTest_full.log` | Full verbose forge output for LocalVaultTest suite. |
| `ufarm/execution_logs/pytest.log` | Integration gate: **4 passed, 1 skipped** in 1.57s (`test_local_fracture_forge_passes`, sigmoid/STE source checks). |
| `ufarm/foundry_sandbox/LocalVaultTest.t.sol` | Concrete Solidity validation payload reconstructing UFarm arithmetic-friction fracture at 2^64 wei. |
| `ufarm/foundry_sandbox/foundry.toml` | Foundry project config used in empirical audit sandbox. |
| `ufarm/evidence/halmos_2pow64_bytecode_evidence.json` | Bytecode analysis confirming `0x10000000000000000` present in compiled Halmos test artifact. |
| `ufarm/evidence/README_EVIDENCE.txt` | Evidence chain description for Halmos/bytecode artifacts. |
| `ufarm/source_snapshots/test_ufarm_gradient_convergence.py` | Standalone script reproducing BPTT-style Adam profit maximization (source of `gradient_convergence.log`). |
| `ufarm/source_snapshots/run_empirical_audit.sh` | Shell driver for audit campaign (historical; do not re-run for submission). |

### DVD Calibration (`dvd_calibration/`)

#### Energy Schemas (`energy_schemas/`)

| File | Target | Routing Flag |
|------|--------|--------------|
| `unstoppable_jepa_energy_schema.json` | UnstoppableVault | `VAULT_ACCOUNTING_DESYNC` — ERC4626 share/asset equality fracture |
| `puppet-v2_jepa_energy_schema.json` | PuppetV2Pool | `AMM_ORACLE_MANIPULATION` — Uniswap V2 spot oracle crush |
| `side-entrance_jepa_energy_schema.json` | SideEntranceLenderPool | Flash-loan ledger desync |
| `selfie_jepa_energy_schema.json` | SelfiePool / governance | Governance flash-loan lap |
| `truster_jepa_energy_schema.json` | TrusterLenderPool | Arbitrary call during flash loan |

These JSON files define the **non-linear invariant energies** the Critic node optimizes against during BPTT.

#### Slither Ingest Cache (`slither_cache/`)

| File | Demonstrates |
|------|--------------|
| `puppet-v2_slither_ingest.json` | Native Slither `--json` output ingested at JEPA perception; detectors on `borrow()`. |
| `side-entrance_slither_ingest.json` | Slither features for `flashLoan()` reentrancy-class detectors. |
| `truster_slither_ingest.json` | Slither features for Truster flash-loan surface. |

#### Exploit Scaffolds (`exploit_scaffolds/`)

| File | Demonstrates |
|------|--------------|
| `unstoppable_Exploit.t.sol` | **JEPAExploitTest:** ERC4626 direct-transfer desync halts flash loan; validates `VAULT_ACCOUNTING_DESYNC` routing. |
| `puppet-v2_Exploit.t.sol` | **JEPAExploitTest:** AMM constant-product manipulation → undercollateralized borrow; validates `AMM_ORACLE_MANIPULATION`. |
| `puppet-v2_JEPAAutoTunnel.t.sol` | Full Foundry exploit scaffold (identical logic path to Exploit.t.sol) emitted post energy convergence. |
| `unstoppable_JEPAAutoTunnel.t.sol` | Unstoppable-specific JEPA tunnel scaffold with vault desync test. |
| `side-entrance_JEPAAutoTunnel.t.sol` | Side-entrance probe scaffold (semantic tube seed). |
| `selfie_JEPAAutoTunnel.t.sol` | Selfie governance-lap probe scaffold. |
| `inject_side_entrance_exploit.py` | Translator helper: injects `SideEntranceExploit` contract into DfD test harness. |
| `inject_selfie_exploit.py` | Translator helper for Selfie challenge exploit injection. |

> **Note on naming:** The CLI writes `artifacts/pocs/Exploit_<target>_<timestamp>.t.sol` on successful hunts. The workspace `artifacts/pocs/` directory is currently empty on this host; historical PoCs are preserved here as `Exploit.t.sol` / `JEPAAutoTunnel.t.sol` scaffolds under calibration targets.

#### Scan Reports (`scan_reports/`)

| File | Demonstrates |
|------|--------------|
| `reports_dvdefi_REGRESSION_VALIDATION_20260205.md` | Slither pipeline regression across 18 DVD challenges; documents detection variance and calibration motivation. |
| `reports_dvdefi_dvdefi_scan_20260205_193401.md` | Point-in-time Slither scan snapshot (unstoppable, naive-receiver, truster, side-entrance, puppet-v2, selfie, etc.). |

### Integration Tests (`integration_tests/`)

| File | Demonstrates |
|------|--------------|
| `test_jepa_dvd_calibration.py` | Unit proofs: vault integer STE, router energy scaling, perception mapper on calibration schemas (unstoppable, puppet-v2). |
| `test_ufarm_empirical_audit.py` | CI gate tying sigmoid/STE source presence → Halmos bytecode → forge pass. |

---

## Core Metrics Displayed

These logs prove **mathematical convergence on non-linear logic flaws** under strict local hardware constraints:

| Metric | Value | Source |
|--------|-------|--------|
| Adam learning rate | **0.01** | Production default (`nodes.py` BPTT critic) |
| BPTT inner steps | **10** per MPC lap | `JEPA_MAX_BPTT_STEPS` default |
| Energy router threshold | **0.82** | Routes to Translator + Foundry |
| MPC outer cap | **100** iterations | `JEPA_MAX_MPC_ITERATIONS` |
| PyTorch thread cap | **2** | Deliberate under-threading on 8-vCPU host |
| Gradient convergence epochs | **90** logged | `gradient_convergence.log` |
| Final optimized profit (PyTorch) | **8.048×10¹⁸ wei** | `gradient_convergence.log` |
| Foundry `testLocalFracture` profit | **2.5×10¹⁸ wei** | `forge_testLocalFracture.log` |
| 2^64 wei ground truth | **18446744073709551616** | `halmos_2pow64_bytecode_evidence.json` |
| Pytest integration | **4/4 passed** (1 skipped) | `pytest.log` |
| Spatial footprint | **O(1)** fixed latent dim (32–256) + 8-dim Slither feature vector per contract; ILG tensors cached to `.pt` without full AST materialization in state | Architecture design per `JEPA_Architecture_Evolution_Report.md` |

**Hardware context:** Campaign executed on local **8-vCPU** VPS with PyTorch deliberately capped at 2 OpenMP threads, leaving headroom for Foundry subprocesses. Memory-bound BPTT loops operate on fixed-dimension tensors rather than full contract bytecode in RAM.

---

## How to Use This Package (Reviewers)

1. **Start with architecture:** Read `architecture/jepa_evm_graph.py` for the control-flow graph.
2. **UFarm proof chain:** `VERAPTOS_EMPIRICAL_AUDIT_PROOF.md` → `gradient_convergence.log` → `forge_testLocalFracture.log`.
3. **DVD calibration:** Pick a challenge schema (e.g. `puppet-v2_jepa_energy_schema.json`) and match to its `*_Exploit.t.sol` scaffold.
4. **Do not re-execute** forge/pytest commands unless reproducing locally; all evidence is pre-captured.

---

## Provenance

| Campaign | Original path |
|----------|---------------|
| UFarm empirical audit | `archives/campaign_veraptos_v3_empirical_audit_ufarm_2pow64_2026-05-22/` |
| DVD calibrations | `targets/web3/calibration/{unstoppable,puppet-v2,side-entrance,selfie,truster}/` |
| JEPA graph | `services/swarm-director/agents/jepa_evm/graph.py` |
