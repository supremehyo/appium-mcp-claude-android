from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List

from .action_types import PlanResponse, PlannedAction

logger = logging.getLogger(__name__)


try:
    import anthropic
except ImportError:  # pragma: no cover - optional dependency
    anthropic = None  # type: ignore[assignment]


@dataclass
class LLMClient:
    """Produces structured action plans from prompts."""

    provider: str = "mock"
    model: str = "claude-3-5-sonnet-20240620"
    temperature: float = 0.0

    def plan_actions(
        self, prompt: str, fallback_nodes: Iterable[Dict[str, Any]] | None = None
    ) -> PlanResponse:
        if self.provider == "anthropic":
            return self._call_anthropic(prompt)
        return self._mock_actions(fallback_nodes, prompt)

    def _call_anthropic(self, prompt: str) -> PlanResponse:
        if anthropic is None:
            raise RuntimeError("anthropic package not installed. Install dependencies or switch provider.")

        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError("ANTHROPIC_API_KEY is not set")

        client = anthropic.Anthropic(api_key=api_key)
        message = client.messages.create(
            model=self.model,
            max_tokens=1000,
            temperature=self.temperature,
            messages=[{"role": "user", "content": prompt}],
        )

        content = next((block.text for block in message.content if block.type == "text"), "{}")
        payload = json.loads(content)
        return PlanResponse.from_payload(payload)

    def _mock_actions(
        self, nodes: Iterable[Dict[str, Any]] | None, prompt: str
    ) -> PlanResponse:
        """Enhanced heuristic that analyzes actual screen elements."""

        node_list = list(nodes or [])
        logger.info("Mock provider analyzing %d screen elements", len(node_list))
        actions: List[PlannedAction] = []
        request = prompt.lower()

        # Extract keywords from the request
        keywords = self._extract_keywords(request)
        logger.info("Extracted keywords from request: %s", keywords)

        # Search through actual screen nodes
        if node_list:
            # Try to find a matching element
            target = self._find_best_match(node_list, keywords, request)

            if target:
                text_value = target.get("text") or target.get("content_desc")
                logger.info("Found matching element: text='%s', content_desc='%s', resource_id='%s'",
                           target.get("text"), target.get("content_desc"), target.get("resource_id"))

                # Determine action type
                if "입력" in request or "input" in request or "type" in request:
                    actions.append(
                        PlannedAction(
                            name="input_text",
                            locator={"strategy": "node_index", "value": target.get("index", 1)},
                            value="",  # Empty for now, would need to extract from prompt
                            metadata={"mock_reason": "input field matched", "element": str(target)},
                        )
                    )
                else:
                    # Default to tap
                    actions.append(
                        PlannedAction(
                            name="tap",
                            locator={"strategy": "node_index", "value": target.get("index", 1)},
                            metadata={"mock_reason": "keyword matched", "element": str(target)},
                        )
                    )
            else:
                logger.warning("No matching element found for keywords: %s", keywords)
                actions.append(PlannedAction(name="noop", metadata={"mock_reason": "no match found"}))
        else:
            logger.warning("No screen elements available")
            actions.append(PlannedAction(name="noop", metadata={"mock_reason": "no nodes"}))

        return PlanResponse(actions=actions, request_refresh=False, thought="Mock response")

    def _extract_keywords(self, request: str) -> List[str]:
        """Extract searchable keywords from the request."""
        # Extract only the user request part if it's a full prompt
        if "User request:" in request or "user request:" in request:
            parts = request.split("user request:")
            if len(parts) > 1:
                request = parts[-1].strip()
                logger.info("Extracted user request: %s", request)

        # Remove common Korean particles and words
        stop_words = {"를", "을", "에", "에서", "의", "로", "으로", "과", "와", "이", "가", "은", "는",
                     "현재", "화면", "버튼", "클릭", "눌러", "눌러줘", "해줘", "주세요", "수", "있습니다"}

        words = request.split()
        keywords = [w for w in words if w not in stop_words and len(w) > 1]
        return keywords

    def _find_best_match(
        self, nodes: Iterable[Dict[str, Any]], keywords: List[str], full_request: str
    ) -> Dict[str, Any] | None:
        """Find the best matching element based on keywords."""
        best_match = None
        best_score = 0

        # Extract user request if embedded in prompt
        user_request = full_request
        if "user request:" in full_request.lower():
            parts = full_request.lower().split("user request:")
            if len(parts) > 1:
                user_request = parts[-1].strip()

        for node in nodes:
            text = (node.get("text") or "")
            text_lower = text.lower()
            content_desc = (node.get("content_desc") or "").lower()
            resource_id = (node.get("resource_id") or "").lower()

            # Skip empty nodes
            if not text and not content_desc:
                continue

            score = 0

            # Exact phrase match gets highest priority
            combined_keywords = " ".join(keywords).replace("을", "").replace("를", "").replace("에서", "").strip()
            if combined_keywords.lower() in text_lower:
                score += 100
                logger.info("Exact phrase match found: '%s' contains '%s'", text, combined_keywords)

            # Individual keyword matches
            for keyword in keywords:
                keyword_lower = keyword.lower().replace("을", "").replace("를", "").replace("에서", "")
                if keyword_lower in text_lower:
                    score += 10
                if keyword_lower in content_desc:
                    score += 8
                if keyword_lower in resource_id:
                    score += 5

            # Shorter text gets bonus (more likely to be the target)
            if score > 0 and len(text) < 20:
                score += 5

            # Update best match
            if score > best_score:
                best_score = score
                best_match = node
                logger.info("New best match: '%s' (score: %d)", text, score)

        logger.info("Final best match score: %d", best_score)
        return best_match


def _match_node(nodes: Iterable[Dict[str, Any]] | None, *expectations: tuple[str, str]):
    if not nodes:
        return None

    for node in nodes:
        for key, value in expectations:
            candidate = (node or {}).get(key)
            if candidate and value.lower() in candidate.lower():
                return node
    return None


def _match_first(nodes: Iterable[Dict[str, Any]] | None):
    if not nodes:
        return None
    for node in nodes:
        if node.get("text") or node.get("content_desc"):
            return node
    return None
