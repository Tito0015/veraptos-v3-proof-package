"""
UFarm empirical audit — reproducible checks for the Veraptos optimization proof.

Validates (from local codebase only):
1. Sigmoid relaxation + BPTT loop exist in jepa_evm.nodes
2. STE pattern in _v2_translation_raw_energy (VAULT_ACCOUNTING_DESYNC)
3. Foundry testLocalFracture positive profit (subprocess, skipped if forge missing)
4. 2^64 constant present in UFarm Halmos artifact bytecode (if present)
"""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
GIST = REPO / "local_sandbox_gist"
HALMOS_ARTIFACT = (
    REPO
    / "targets"
    / "web3"
    / "ufarm"
    / "out"
    / "UFarmSignalLagHalmos.t.sol"
    / "UFarmSignalLagHalmosTest.json"
)
TWO_POW_64_HEX = format(2**64, "x")  # 10000000000000000


def test_sigmoid_relaxation_source_present():
    """Audit point 1: continuous relaxation via sigmoid in BPTT critic."""
    nodes_py = REPO / "services" / "swarm-director" / "agents" / "jepa_evm" / "nodes.py"
    text = nodes_py.read_text(encoding="utf-8")
    assert "p_valid = torch.sigmoid(c_z_a / temp_t)" in text
    assert "e_next = p_exp * hallucinated + (1.0 - p_exp) * z" in text
    assert "loss.backward()" in text
    assert "optimizer.step()" in text


def test_ste_pattern_source_present():
    """Audit point 1b: STE for vault integer desync."""
    nodes_py = REPO / "services" / "swarm-director" / "agents" / "jepa_evm" / "nodes.py"
    text = nodes_py.read_text(encoding="utf-8")
    assert "diff_int_t.detach() + (diff_soft - diff_soft.detach())" in text


@pytest.mark.skipif(not HALMOS_ARTIFACT.is_file(), reason="UFarm Halmos artifact not on disk")
def test_two_pow_64_in_halmos_bytecode():
    """Audit point 3: 2^64 wei boundary constant in compiled UFarm test bytecode."""
    data = json.loads(HALMOS_ARTIFACT.read_text(encoding="utf-8"))
    bytecode = data.get("bytecode", {}).get("object", "") or data.get("deployedBytecode", {}).get("object", "")
    assert TWO_POW_64_HEX in bytecode.lower(), (
        f"Expected 2^64 hex {TWO_POW_64_HEX} in UFarmSignalLagHalmos bytecode"
    )


@pytest.mark.skipif(
    subprocess.run(["which", "forge"], capture_output=True).returncode != 0,
    reason="forge not installed",
)
def test_local_fracture_forge_passes():
    """Audit point 3: testLocalFracture extracts profit > 0 wei."""
    assert (GIST / "test" / "LocalVaultTest.t.sol").is_file()
    proc = subprocess.run(
        [
            "forge",
            "test",
            "--match-test",
            "testLocalFracture",
            "-vv",
        ],
        cwd=str(GIST),
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "PROFIT EXTRACTED:" in proc.stdout + proc.stderr
    assert re.search(r"Extracted profit \(wei\):\s*(\d+)", proc.stdout + proc.stderr)


def test_ufarm_gradient_convergence_script():
    """Audit point 2: PyTorch profit maximization and STE/sigmoid demos."""
    script = GIST / "test_ufarm_gradient_convergence.py"
    if not script.is_file():
        pytest.skip("gradient convergence script missing")

    venv_python = GIST / ".venv-ste" / "bin" / "python"
    if venv_python.is_file():
        check = subprocess.run(
            [str(venv_python), "-c", "import torch"],
            capture_output=True,
        )
        if check.returncode != 0:
            pytest.skip("torch not in .venv-ste")
        python = str(venv_python)
    else:
        pytest.importorskip("torch")
        python = "python3"
    proc = subprocess.run(
        [python, str(GIST / "test_ufarm_gradient_convergence.py")],
        cwd=str(GIST),
        capture_output=True,
        text=True,
        timeout=180,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "SUCCESS: Gradient descent found profitable boundary" in proc.stdout
    assert "SUCCESS: STE gradient flow validated" in proc.stdout
    assert "SUCCESS: Sigmoid relaxation gradient flow validated" in proc.stdout
