from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict


@dataclass
class AppiumConfig:
    """Holds Appium server URL and desired capabilities."""

    server_url: str
    capabilities: Dict[str, Any] = field(default_factory=dict)
    adb_binary: str = "adb"
    use_accessibility_dump: bool = False

    @classmethod
    def from_file(cls, path: str | Path) -> "AppiumConfig":
        payload = json.loads(Path(path).read_text())
        return cls(
            server_url=payload["server_url"],
            capabilities=payload.get("capabilities", {}),
            adb_binary=payload.get("adb_binary", "adb"),
            use_accessibility_dump=payload.get("use_accessibility_dump", False),
        )

    def to_prompt_payload(self) -> Dict[str, Any]:
        """Expose minimal configuration that may be useful in prompts."""

        return {
            "platformName": self.capabilities.get("platformName", "unknown"),
            "automationName": self.capabilities.get("automationName", "uiautomator2"),
            "appPackage": self.capabilities.get("appPackage"),
            "appActivity": self.capabilities.get("appActivity"),
        }
