"""
Compile `StateGraph(VeraptosState)` for the JEPA-EVM six-node deterministic pipeline.
"""

from __future__ import annotations

import logging
import os
from typing import Any, Dict

import numpy as np
from langgraph.graph import END, StateGraph

from .block_pin import require_strict_fork_block
from .hardware_env import configure_torch_hardware
from .nodes import (
    critic_energy_gate_node,
    critic_energy_router,
    hil_foundry_execution_node,
    jepa_latent_mpc_node,
    perception_mapper_node,
    reality_backprop_node,
    reality_router,
    translator_llm_node,
)
from .veraptos_state import VeraptosState, empty_ilg_topology

logger = logging.getLogger(__name__)


def create_jepa_evm_initial_state(
    *,
    latent_dim: int | None = None,
    contract_ast: Dict[str, Any] | None = None,
) -> VeraptosState:
    """
    Seed dictionary before `START -> Perception_Mapper`.

    Normally `contract_ast` is left empty — Node 1 overwrites topology fields.
    """
    dim = latent_dim if latent_dim is not None else int(os.environ.get("JEPA_LATENT_DIM", "32"))
    dim = max(8, min(dim, 256))
    z0 = np.full(dim, 0.02, dtype=np.float32)
    blank = np.zeros(dim, dtype=np.float32)

    init: VeraptosState = {
        "contract_ast": contract_ast or {},
        "ilg_topology": empty_ilg_topology(),
        "latent_state": blank,
        "action_trajectory": [np.zeros(dim, dtype=np.float32)],
        "latent_uncertainty": z0,
        "predicted_next_state": blank.copy(),
        "energy_score": 0.0,
        "semantic_tube": [],
        "solidity_poc": "",
        "foundry_feedback": "",
        "mpc_iterations": 0,
    }
    return init


def compile_jepa_evm_graph(checkpointer: Any | None = None) -> Any:
    """
    Build and compile LangGraph workflow per architecture JEPA.md.

    Optional `checkpointer` (e.g. MemorySaver) — ndarray fields may require
    custom serializers for Postgres checkpoints.
    """
    require_strict_fork_block()
    configure_torch_hardware()

    workflow = StateGraph(VeraptosState)

    workflow.add_node("Perception_Mapper", perception_mapper_node)
    workflow.add_node("JEPA_Latent_MPC", jepa_latent_mpc_node)
    workflow.add_node("Critic_Energy_Gate", critic_energy_gate_node)
    workflow.add_node("Translator_LLM", translator_llm_node)
    workflow.add_node("HIL_Foundry_Execution", hil_foundry_execution_node)
    workflow.add_node("Reality_Backprop", reality_backprop_node)

    workflow.set_entry_point("Perception_Mapper")
    workflow.add_edge("Perception_Mapper", "JEPA_Latent_MPC")
    workflow.add_edge("JEPA_Latent_MPC", "Critic_Energy_Gate")

    workflow.add_conditional_edges(
        "Critic_Energy_Gate",
        critic_energy_router,
        {
            "high_energy_found": "Translator_LLM",
            "low_energy_continue": "JEPA_Latent_MPC",
            "mpc_exhausted": END,
        },
    )

    workflow.add_edge("Translator_LLM", "HIL_Foundry_Execution")
    workflow.add_edge("HIL_Foundry_Execution", "Reality_Backprop")

    workflow.add_conditional_edges(
        "Reality_Backprop",
        reality_router,
        {
            "revert_rejected": "JEPA_Latent_MPC",
            "exploit_verified": END,
            "mpc_exhausted": END,
        },
    )

    if checkpointer is not None:
        app = workflow.compile(checkpointer=checkpointer)
    else:
        app = workflow.compile()

    logger.info("[JEPA-EVM] compiled 6-node graph (checkpointer=%s)", checkpointer is not None)
    return app


def run_jepa_evm_once(
    initial: VeraptosState | Dict[str, Any] | None = None,
    *,
    checkpointer: Any | None = None,
    thread_id: str = "jepa-default",
) -> Dict[str, Any]:
    """Compile + `invoke` to completion (returns final merged state)."""
    app = compile_jepa_evm_graph(checkpointer=checkpointer)
    seed: Dict[str, Any] = dict(initial) if initial is not None else dict(create_jepa_evm_initial_state())
    # LangGraph default recursion_limit=25 is too low for JEPA MPC (see run_calibration.py: 500)
    recursion_limit = int(os.environ.get("JEPA_RECURSION_LIMIT", "500"))
    cfg: Dict[str, Any] = {
        "configurable": {"thread_id": thread_id},
        "recursion_limit": recursion_limit,
    }
    return app.invoke(seed, cfg)
