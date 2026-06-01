# JEPA Architecture Evolution Report

**Veraptos Class 3 Cyber Factory — Pipeline Upgrade Summary**  
**Last updated:** 2026-04-29  
**Scope:** Transition from Medusa-centric fuzzing to the JEPA-EVM deterministic LangGraph factory (hardware-conscious, mainnet-groundable).

---

## 1. From pure Medusa fuzzing to the Class 3 JEPA-EVM Factory

**Baseline:** Operation Bitexen used Medusa (property-based EVM fuzzing) from a dedicated Foundry workspace (`exen_medusa_workspace`). Medusa explores concrete transactions against deployed or forked bytecode and accumulates corpus artifacts.

**Upgrade:** The **JEPA-EVM Factory** adds a **six-node LangGraph** pipeline that is **not** a replacement for fuzzers on day one—it **layers**:

- **Perception** (AST/solidity touchpoints + ILG tensors + observable injection).
- **Latent MPC** (world-model prediction in RAM).
- **Energy critic** (Hamiltonian residuals vs heuristic fallback).
- **Translator LLM** (syntax-only Foundry scaffold).
- **HIL Foundry** (`forge build` / `forge test` against pinned RPC discipline).
- **Reality backprop** (Foundry outcome feeds aleatoric steering).

**Operational constraints baked in:** KVM-8 thermal budget (`torch.set_num_threads(2)`), **no cold `--fork-url`** burst on forge—`**--rpc-url**` to a persistent daemon plus **`--fork-block-number`** aligned with Node 1 RPC block pinning, snapshot/revert in generated tests where applicable.

---

## 2. The JEPA Engine Drop (ARPredictor)

**Location:** `services/swarm-director/agents/jepa_evm/jepa_engine.py`

The **LeWM-style ARPredictor** (from the upstream LeWorldModel stack) performs the latent transition **s_{t+1}** inside Node 2 (`jepa_latent_mpc_node`). Implementation highlights:

- **Singleton predictor** with configurable `latent_dim`, depth, heads, frame count (env-tunable).
- Forward runs under **`torch.no_grad()`** for inference-only MPC loops.
- **Aleatoric injection:** `latent_uncertainty` (**z_t**) is added into the state embedding before the predictor forward pass so Node 6 penalties affect trajectories mathematically.

This replaces the earlier pure-numpy MPC stub for PyTorch-capable environments while retaining a numpy fallback path when torch is unavailable.

---

## 3. The Observable Bridge (Index Slicing and Normalization)

**Modules:** `observable_bridge.py`, `energy_schema.py`, Phase 1 JSON (e.g. `jepa_energy_constraints.*.phase1.json`)

**Problem:** Continuous latent vectors must speak to **discrete on-chain observables** (e.g. `totalSupply`, `INITIAL_SUPPLY`) without training a full decoder for every bounty.

**Solution:**

1. **Fixed index map:** Each observable in the energy schema gets a **fixed latent index** (explicit `latent_index` in JSON where defined).
2. **Normalization:** EVM-scale uints map to **[-1, 1] float32** via `normalize_evm_value(raw, scale)` using a declared scale (e.g. `INITIAL_SUPPLY_RAW`).
3. **Node 3 critic:** Slices predicted **s_{t+1}** at those indices, **denormalizes**, evaluates **Hamiltonian** string expressions via **`safe_eval_hamiltonian`** (restricted namespace), aggregates weighted residuals into **`energy_score`**.

This yields a **stable, zero-shot bridge** between JSON constraints and tensor telemetry.

---

## 4. Brownian Steering (Aleatoric Friction)

**Location:** `reality_backprop_node` in `nodes.py`; thresholds in `thresholds.py`

**Anti-pattern avoided:** Adding a **scalar** penalty directly to every dimension of **z_t** produces diagonal drift (embedding blow-up).

**Correct mechanics:** On Foundry negative signal, update:

`z ← z + μ · noise_direction`

where **noise_direction** is **unit-variance Gaussian** per dimension batch and **μ** comes from **`ALEATORIC_PENALTY_MU`** (env `JEPA_ALEATORIC_PENALTY_MU`, default ~0.03). This implements **Brownian steering**: localized exploration away from failed paths without systematic inflation.

---

## 5. Strict Block Pinning

**Module:** `block_pin.py`  
**Integration:** `graph.compile_jepa_evm_graph()` calls **`require_strict_fork_block()`** before compilation.

**Rules:**

- **`JEPA_FORK_BLOCK`** must be a **concrete positive integer** (decimal or `0x` hex).
- **Forbidden:** `latest`, `pending`, `earliest`, `safe`, `finalized`, empty/missing (when strict gate applies).

**Alignment:**

- **Node 1:** `rpc_grounding.fetch_live_erc20_observables` passes **`fork_block_hex_for_eth_call()`** into **`eth_call`** so **totalSupply**, **INITIAL_SUPPLY**, and **balanceOf** witnesses read **the same historical block**.
- **Node 5:** **`forge test`** appends **`--fork-block-number`** alongside **`--rpc-url`** so Foundry executes against the **same** pinned snapshot as Python RPC grounding.

**FastAPI:** When **`JEPA_ETH_RPC_HTTP`** is set at startup, **`main.py`** lifespan validates **`JEPA_FORK_BLOCK`** so misconfigured env fails before serving.

---

## 6. References (in-repo)

| Artifact | Role |
|----------|------|
| `agents/jepa_evm/graph.py` | Six-node graph wiring |
| `agents/jepa_evm/nodes.py` | All node semantics + forge CLI |
| `agents/jepa_evm/observable_bridge.py` | Normalize/denormalize/safe eval |
| `agents/jepa_evm/rpc_grounding.py` | eth_call selectors + witnesses |
| `agents/jepa_evm/block_pin.py` | Fork block parse/require |
| `scripts/run_calibration.py` | Stream graph; peak energy + τ suggestion |
| `docs/PHASE2_OBSERVABLE_BRIDGE_COMPLETION.md` | Phase 2 bridge completion notes |

---

## 7. Archive note (post–Operation Bitexen)

The Bitexen target tree and energy schema JSON are archived under **`archive/operation-bitexen/operation-exen/`**. Update any absolute paths in downstream tooling to that location or set **`JEPA_ENERGY_SCHEMA_PATH`** explicitly for the next bounty target.
