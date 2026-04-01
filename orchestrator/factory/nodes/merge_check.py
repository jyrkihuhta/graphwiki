"""Merge check node: verify all PRs have been merged before finalization."""

import json
import logging
import subprocess

from ..state import FactoryState

logger = logging.getLogger(__name__)


async def merge_check_node(state: FactoryState) -> dict:
    """Confirm that all subtask PRs have been merged into the main branch.

    Uses the ``gh`` CLI to check each subtask PR that is in ``"review"``
    status.  If GitHub reports the PR as ``MERGED``, the subtask status is
    updated to ``"merged"``.

    Args:
        state: Current FactoryState after pm_review / human_review_code.

    Returns:
        Partial state update with the updated ``subtasks`` list.
    """
    logger.info(
        "merge_check: verifying PR merges for task %s",
        state.get("task_wiki_page", "<unknown>"),
    )
    subtasks = list(state["subtasks"])
    for i, subtask in enumerate(subtasks):
        if subtask.get("pr_number") and subtask["status"] == "review":
            result = subprocess.run(
                [
                    "gh",
                    "pr",
                    "view",
                    str(subtask["pr_number"]),
                    "--json",
                    "state,mergedAt",
                ],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                data = json.loads(result.stdout)
                if data.get("state") == "MERGED":
                    logger.info(
                        "merge_check: PR #%s is merged for subtask %s",
                        subtask["pr_number"],
                        subtask["id"],
                    )
                    subtasks[i] = {**subtask, "status": "merged"}
    return {"subtasks": subtasks}
