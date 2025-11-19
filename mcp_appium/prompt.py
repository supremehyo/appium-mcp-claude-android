from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

from .node_parser import NodeSnapshot, summarize_nodes


PROMPT_TEMPLATE = """You are an expert Appium test agent that works in iterative steps.
Each turn you receive:
1. Device/app configuration details.
2. Snapshot of the current UI nodes (each line is indexed; refer to them via `locator.strategy="node_index"` and provide the matching index).
3. The original natural language request from the user.
4. Execution history from previous steps (if any).

Return a valid JSON object:
{{
  "thought": "<short reasoning>",
  "actions": [
     {{
        "name": "tap" | "input_text" | "wait" | "swipe" | "assert_text" | "long_press" | "back" | "scroll_down" | "scroll_up",
        "locator": {{"strategy": "node_index|id|accessibility_id|xpath|android_uiautomator|ios_predicate|text|coordinates", "value": "<locator value>"}},
        "value": "<text for input/assertion or 'x,y' coordinates>",
        "metadata": {{"duration_ms": <duration in milliseconds for long_press>, "end": "<x,y end coordinates for swipe>"}}
     }}
  ],
  "request_refresh": true | false
}}

Guidelines:
- Prefer `node_index` whenever the target exists in the node list; fallback to other strategies only if necessary.
- Keep actions deterministic and directly related to fulfilling the request. At most 3 actions per response.
- Set `request_refresh=true` when more steps are needed after executing these actions; otherwise false when the goal is complete.
- Use `assert_text` to validate expected results, and `wait` only when essential (value in seconds).

Configuration:
{config}

Current UI nodes (limit={limit}):
{nodes}

Execution history (latest first):
{history}

User request:
{request}
"""


@dataclass
class PromptBuilder:
    device_info: Dict[str, str]
    node_limit: int = 40

    def build(self, request: str, nodes: list[NodeSnapshot], history: str) -> str:
        return PROMPT_TEMPLATE.format(
            config=self.device_info,
            limit=self.node_limit,
            nodes=summarize_nodes(nodes, limit=self.node_limit) or "<no nodes available>",
            history=history or "<empty>",
            request=request,
        )
