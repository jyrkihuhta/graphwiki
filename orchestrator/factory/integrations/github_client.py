"""GitHub API client for the factory orchestrator."""

from __future__ import annotations

import logging
import subprocess

logger = logging.getLogger(__name__)


class GitHubClient:
    """GitHub client for fetching pull request information.

    Uses the ``gh`` CLI tool for PR operations, which must be authenticated
    on the machine running the orchestrator.
    """

    async def get_pr_diff(self, pr_number: int) -> str:
        """Fetch the unified diff for a pull request using the gh CLI.

        Args:
            pr_number: GitHub pull request number.

        Returns:
            Unified diff as a string, or the stderr output if the command fails.
        """
        result = subprocess.run(
            ["gh", "pr", "diff", str(pr_number)],
            capture_output=True,
            text=True,
        )
        return result.stdout or result.stderr
