"""Armory artifact prompts and constants for the factory grinder.

Contains system-level documentation and constraints injected into grinder
task prompts for Molly armory artifact types (tool, playbook, wordlist).
Also exports FORBIDDEN_IMPORTS used by validate_armory_node.
"""

from __future__ import annotations

FORBIDDEN_IMPORTS: frozenset[str] = frozenset(
    {
        "urllib",
        "requests",
        "httpx",
        "aiohttp",
        "socket",
        "http.client",
    }
)

# ---------------------------------------------------------------------------
# Tool protocol documentation
# ---------------------------------------------------------------------------

TOOL_PROTOCOL = """\
## Molly Tool Protocol

Every Molly tool is a Python class that:
1. Inherits from `ToolBase` (imported from `molly.tools.base`).
2. Defines a class attribute `capability_name: str` — a short snake_case identifier
   (e.g. `"jwt_forge"`, `"nuclei_scan"`).
3. Implements `name(self) -> str` — human-readable tool name.
4. Implements `description(self) -> str` — one sentence describing what the tool does.
5. Implements `parameters_schema(self) -> dict` — returns an OpenAI function-calling
   JSON schema dict with `"type": "object"`, `"properties"`, and `"required"` keys.
6. Implements `async execute(self, **kwargs) -> dict` — performs the attack and returns
   a result dict.  Raise `ToolError` on unrecoverable errors.

### Forbidden imports — NEVER use these modules in execute():
- `urllib`, `urllib.request`, `urllib.parse`
- `requests`, `httpx`, `aiohttp`
- `socket`, `http.client`

Reason: Molly provides a managed HTTP client.  Use the `client` keyword argument
injected by the runner if you need to make HTTP requests.

### ToolError
Raise `molly.tools.base.ToolError` for expected failure modes (e.g. target unreachable,
invalid response).  Do not use bare `Exception` for recoverable errors.

### Example skeleton:
```python
from molly.tools.base import ToolBase, ToolError


class MyTool(ToolBase):
    capability_name = "my_tool"

    def name(self) -> str:
        return "My Tool"

    def description(self) -> str:
        return "Does something to the target endpoint."

    def parameters_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "Target URL."},
            },
            "required": ["url"],
        }

    async def execute(self, *, url: str, client=None, **kwargs) -> dict:
        if client is None:
            raise ToolError("No HTTP client provided")
        resp = await client.get(url)
        return {"status": resp.status_code, "body": resp.text[:1000]}
```
"""

# ---------------------------------------------------------------------------
# Playbook schema documentation
# ---------------------------------------------------------------------------

PLAYBOOK_SCHEMA = """\
## Molly Playbook Schema

A Molly playbook is a Markdown file (.md) with YAML frontmatter and a `checks:` YAML
block in the body.

### Frontmatter (required fields):
```yaml
---
playbook: <slug>          # unique snake_case identifier, e.g. jwt-algorithm-confusion
name: <Human Name>        # display name
leaf_type: <type>         # endpoint category this applies to, e.g. auth_endpoint
applies_to:               # list of tags that trigger this playbook
  - auth
  - jwt
---
```

### Checks block (required):
```yaml
checks:
  - id: check_slug              # unique within this playbook
    name: Check display name
    mode: intruder              # intruder | forge | analytical | oob
    category: auth              # auth | injection | ssrf | info | logic | config
    severity: critical          # critical | high | medium | low | info
    # Optional fields:
    requires_capabilities:
      - jwt_forge
    technique: "Description of the attack technique."
    mutations:
      - payload1
      - payload2
    win_condition: "What constitutes a successful finding."
```

### Validation rules:
- `playbook`, `name`, and `leaf_type` are required in frontmatter.
- At least one check must be defined.
- Each check must have `id`, `name`, `mode`, `category`, and `severity`.
- `mode` must be one of: `intruder`, `forge`, `analytical`, `oob`.
- `severity` must be one of: `critical`, `high`, `medium`, `low`, `info`.
- All YAML must be syntactically valid.
"""

# ---------------------------------------------------------------------------
# Wordlist format documentation
# ---------------------------------------------------------------------------

WORDLIST_FORMAT = """\
## Molly Wordlist Format

A Molly wordlist is a plain-text file (.txt) with one entry per line.

Rules:
- UTF-8 encoding.
- One path, payload, or word per line.
- No trailing whitespace.
- Lines starting with `#` are comments (ignored by the scanner).
- Empty lines are ignored.
- Keep entries focused: quality over quantity.
- Include a comment block at the top explaining the purpose and source of the entries.

Example (`sensitive-paths.txt`):
```
# Sensitive file paths for directory enumeration
# Sources: common misconfigurations, OWASP, HackerOne disclosures
.env
.git/config
backup.zip
config.php.bak
```
"""

# ---------------------------------------------------------------------------
# Convenience accessor
# ---------------------------------------------------------------------------

_ARTIFACT_PROMPTS: dict[str, str] = {
    "tool": TOOL_PROTOCOL,
    "playbook": PLAYBOOK_SCHEMA,
    "wordlist": WORDLIST_FORMAT,
}


def get_armory_prompt(artifact_type: str | None) -> str:
    """Return the armory protocol/schema documentation for *artifact_type*.

    Args:
        artifact_type: One of ``"tool"``, ``"playbook"``, ``"wordlist"``, or
            ``None`` / ``"code"`` for MeshWiki tasks (returns empty string).

    Returns:
        Multi-line documentation string to embed in the grinder task prompt,
        or an empty string for non-armory artifact types.
    """
    if artifact_type is None or artifact_type == "code":
        return ""
    return _ARTIFACT_PROMPTS.get(artifact_type, "")
