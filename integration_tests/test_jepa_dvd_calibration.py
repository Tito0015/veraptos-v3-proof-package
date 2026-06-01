"""
DVD calibration remediation tests: vault integer STE, schema router_denominator, AMM coupling.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest
import torch

from agents.jepa_evm.energy_schema import get_global_constants
from agents.jepa_evm.nodes import (
    _router_energy_from_raw_v2,
    _v2_translation_raw_energy,
    perception_mapper_node,
)
from agents.jepa_evm.graph import create_jepa_evm_initial_state


REPO = Path(__file__).resolve().parents[1]


@pytest.fixture(autouse=True)
def _jepa_fork_block_env(monkeypatch):
    monkeypatch.setenv("JEPA_FORK_BLOCK", "21500000")


def _load_calibration_schema(name: str) -> dict:
    path = REPO / "targets" / "web3" / "calibration" / name / "jepa_energy_schema.json"
    assert path.is_file(), path
    return json.loads(path.read_text(encoding="utf-8"))


def test_vault_integer_ste_one_wei_diff():
    schema = _load_calibration_schema("unstoppable")
    gc = get_global_constants(schema)
    e_next = torch.zeros(32, dtype=torch.float32)
    vault = float(gc["VAULT_TOTAL_SUPPLY"])
    delta = float(gc["DESYNC_DELTA"])
    action_2d = torch.nn.Parameter(
        torch.tensor([vault, vault + delta], dtype=torch.float64),
        requires_grad=True,
    )
    raw = _v2_translation_raw_energy(
        e_next,
        schema,
        {},
        "VAULT_ACCOUNTING_DESYNC",
        gc,
        sybil_stub_logged=[False],
        action_2d=action_2d,
    )
    assert float(raw.detach().item()) == pytest.approx(delta, rel=1e-9)
    router = _router_energy_from_raw_v2(
        raw, float(gc["PRICE"]), routing_flag="VAULT_ACCOUNTING_DESYNC", gc=gc
    )
    assert router >= 0.01


def test_router_reads_schema_denominator():
    gc = {"router_denominator": 1e18, "PRICE": 1e18}
    raw = torch.as_tensor(1e18, dtype=torch.float64)
    router = _router_energy_from_raw_v2(
        raw, 1e18, routing_flag="VAULT_ACCOUNTING_DESYNC", gc=gc
    )
    assert router == pytest.approx(1.0, rel=1e-6)


def test_amm_raw_energy_grad_swap():
    schema = _load_calibration_schema("puppet-v2")
    gc = get_global_constants(schema)
    pool_init = float(gc["POOL_INITIAL_TOKENS"])
    action_2d = torch.nn.Parameter(
        torch.tensor([float(gc["SWAP_AMOUNT"]), pool_init * 0.5], dtype=torch.float64),
        requires_grad=True,
    )
    e_next = torch.zeros(32, dtype=torch.float32)
    raw = _v2_translation_raw_energy(
        e_next,
        schema,
        {},
        "AMM_ORACLE_MANIPULATION",
        gc,
        sybil_stub_logged=[False],
        action_2d=action_2d,
    )
    raw.backward()
    assert action_2d.grad is not None
    assert abs(float(action_2d.grad[0].item())) > 0.0


def test_amm_swap_monotone():
    schema = _load_calibration_schema("puppet-v2")
    gc = get_global_constants(schema)
    pool_init = float(gc["POOL_INITIAL_TOKENS"])
    collateral = pool_init * 0.5
    e_next = torch.zeros(32, dtype=torch.float32)

    def energy_for_swap(swap: float) -> float:
        a2 = torch.tensor([swap, collateral], dtype=torch.float64)
        raw = _v2_translation_raw_energy(
            e_next,
            schema,
            {},
            "AMM_ORACLE_MANIPULATION",
            gc,
            sybil_stub_logged=[False],
            action_2d=a2,
        )
        return float(raw.detach().item())

    e_small = energy_for_swap(1e22)
    e_large = energy_for_swap(5e23)
    assert e_large > e_small


def test_amm_router_subthreshold_at_init():
    schema = _load_calibration_schema("puppet-v2")
    gc = get_global_constants(schema)
    pool_init = float(gc["POOL_INITIAL_TOKENS"])
    # Smaller initial swap keeps router sub-threshold (1e22 yields ~0.02 at denom 1e24).
    action_2d = torch.tensor(
        [1e21, pool_init * 0.5],
        dtype=torch.float64,
    )
    e_next = torch.zeros(32, dtype=torch.float32)
    raw = _v2_translation_raw_energy(
        e_next,
        schema,
        {},
        "AMM_ORACLE_MANIPULATION",
        gc,
        sybil_stub_logged=[False],
        action_2d=action_2d,
    )
    router = _router_energy_from_raw_v2(
        raw, float(gc["PRICE"]), routing_flag="AMM_ORACLE_MANIPULATION", gc=gc
    )
    assert router < 0.01


def test_perception_fingerprint_differs_by_contract(tmp_path, monkeypatch):
    from agents.jepa_evm.perception_features import fingerprint_contract_sources

    a = tmp_path / "A.sol"
    b = tmp_path / "B.sol"
    a.write_text("contract A { function foo() external {} }", encoding="utf-8")
    b.write_text("contract B { function bar() external payable {} }", encoding="utf-8")
    assert fingerprint_contract_sources([a]) != fingerprint_contract_sources([b])


def test_perception_mapper_records_fingerprint(monkeypatch, tmp_path):
    sol = tmp_path / "Target.sol"
    sol.write_text("contract Target { uint256 x; function f() external { x++; } }", encoding="utf-8")
    monkeypatch.setenv("JEPA_CONTRACT_ROOT", str(tmp_path))
    monkeypatch.setenv("JEPA_INGEST_CONTRACT", str(sol))
    st = dict(create_jepa_evm_initial_state())
    out = perception_mapper_node(st)  # type: ignore[arg-type]
    meta = out.get("contract_ast") or {}
    assert meta.get("contract_fingerprint") is not None
    assert meta.get("perception_version") == "jepa-perception:v2"
