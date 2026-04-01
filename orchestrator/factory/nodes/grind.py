"""Grind node: grinder agent implements a single subtask."""

from __future__ import annotations

import logging

from ..agents.grinder_agent import grind_subtask
from ..integrations.meshwiki_client import MeshWikiClient
from ..state import FactoryState

logger = logging.getLogger(__name__)


async def grind_node(state: FactoryState) -> dict:
    """Run the grinder agent for the current subtask.

    Looks up the subtask identified by ``_current_subtask_id`` in state,
    invokes the grinder agentic loop, and returns a partial state update
    with the updated subtasks list.

    Args:
        state: Current FactoryState, must contain ``_current_subtask_id``.

    Returns:
        Partial state update with ``subtasks`` list where the current
        subtask is replaced by the updated version from the grinder.
    """
    subtask_id = state.get("_current_subtask_id")
    subtask = next(
        (s for s in state["subtasks"] if s["id"] == subtask_id),
        None,
    )
    if subtask is None:
        logger.error("grind_node: subtask %r not found in state", subtask_id)
        return {}

    logger.info(
        "grind_node: running grinder for subtask %s (task %s)",
        subtask_id,
        state.get("task_wiki_page", "<unknown>"),
    )

    meshwiki_client = MeshWikiClient()
    updated = await grind_subtask(state, subtask, meshwiki_client)

    subtasks = [updated if s["id"] == subtask_id else s for s in state["subtasks"]]
    return {"subtasks": subtasks}
