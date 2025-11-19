from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, Iterable, List, Sequence, Tuple
from xml.etree import ElementTree as ET


BOUNDS_PATTERN = re.compile(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]")


@dataclass
class NodeSnapshot:
    text: str = ""
    content_desc: str = ""
    resource_id: str = ""
    class_name: str = ""
    package: str = ""
    bounds: Tuple[int, int, int, int] = (0, 0, 0, 0)

    def prompt_line(self, index: int) -> str:
        text = self.text or self.content_desc or "<empty>"
        return (
            f"{index}. text='{text}' desc='{self.content_desc or '-'}' "
            f"id='{self.resource_id or '-'}' class='{self.class_name}' bounds={self.bounds}"
        )

    def as_dict(self) -> Dict[str, str | Tuple[int, int, int, int]]:
        return {
            "text": self.text,
            "content_desc": self.content_desc,
            "resource_id": self.resource_id,
            "class_name": self.class_name,
            "bounds": self.bounds,
        }

    def preferred_locator(self) -> Dict[str, str] | None:
        if self.resource_id:
            return {"strategy": "id", "value": self.resource_id}
        if self.content_desc:
            return {"strategy": "accessibility_id", "value": self.content_desc}
        if self.text:
            return {"strategy": "text", "value": self.text}
        return None


class NodeParser:
    """Extracts meaningful node summaries from Appium XML or adb dumps."""

    @staticmethod
    def parse_xml(xml_payload: str) -> List[NodeSnapshot]:
        try:
            tree = ET.fromstring(xml_payload)
        except ET.ParseError:
            return []

        snapshots: List[NodeSnapshot] = []
        for element in tree.iter():
            if not element.attrib:
                continue
            snapshots.append(
                NodeSnapshot(
                    text=element.attrib.get("text", ""),
                    content_desc=element.attrib.get("content-desc", ""),
                    resource_id=element.attrib.get("resource-id", ""),
                    class_name=element.attrib.get("class", ""),
                    package=element.attrib.get("package", ""),
                    bounds=_parse_bounds(element.attrib.get("bounds", "")),
                )
            )
        return snapshots

    @staticmethod
    def parse_accessibility_dump(payload: str) -> List[NodeSnapshot]:
        """Very lightweight parser for `adb shell dumpsys accessibility` output."""

        snapshots: List[NodeSnapshot] = []
        current: NodeSnapshot | None = None

        for line in payload.splitlines():
            stripped = line.strip()
            if stripped.startswith(("View[", "AccessibilityNodeInfo[")):
                if current:
                    snapshots.append(current)
                current = NodeSnapshot()
                continue

            if current is None:
                continue

            if stripped.startswith("text:"):
                current.text = stripped.split(":", 1)[1].strip()
            elif stripped.startswith("contentDescription:"):
                current.content_desc = stripped.split(":", 1)[1].strip()
            elif stripped.startswith("resourceName:"):
                current.resource_id = stripped.split(":", 1)[1].strip()
            elif stripped.startswith("className:"):
                current.class_name = stripped.split(":", 1)[1].strip()
            elif stripped.startswith("packageName:"):
                current.package = stripped.split(":", 1)[1].strip()
            elif stripped.startswith("boundsInScreen:"):
                current.bounds = _parse_bounds_from_dump(stripped)

        if current:
            snapshots.append(current)

        return snapshots


def summarize_nodes(nodes: Sequence[NodeSnapshot], limit: int = 40) -> str:
    excerpt = list(nodes[:limit])
    return "\n".join(node.prompt_line(idx + 1) for idx, node in enumerate(excerpt))


def _parse_bounds(raw: str) -> Tuple[int, int, int, int]:
    match = BOUNDS_PATTERN.search(raw)
    if not match:
        return (0, 0, 0, 0)
    return tuple(int(match.group(i)) for i in range(1, 5))  # type: ignore[return-value]


def _parse_bounds_from_dump(line: str) -> Tuple[int, int, int, int]:
    coords = [int(value) for value in re.findall(r"-?\d+", line)]
    if len(coords) >= 4:
        return tuple(coords[:4])  # type: ignore[return-value]
    return (0, 0, 0, 0)
