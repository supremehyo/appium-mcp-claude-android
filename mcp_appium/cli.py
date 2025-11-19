from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

from .bridge import AppiumBridge
from .config import AppiumConfig
from .llm_client import LLMClient


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Natural-language to Appium bridge CLI")
    parser.add_argument("request", help="Natural-language instruction to execute")
    parser.add_argument(
        "--config",
        default="config/appium.json",
        help="Path to Appium configuration JSON",
    )
    parser.add_argument(
        "--provider",
        default="mock",
        choices=["mock", "anthropic"],
        help="LLM provider to use",
    )
    parser.add_argument(
        "--model",
        default="claude-3-5-sonnet-20240620",
        help="LLM model identifier",
    )
    parser.add_argument(
        "--use-accessibility-dump",
        action="store_true",
        help="Use `adb dumpsys accessibility` for node collection",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        help="Python logging level (INFO, DEBUG, ...)",
    )
    return parser.parse_args()


def build_bridge(args: argparse.Namespace) -> AppiumBridge:
    config_path = Path(args.config)
    if not config_path.exists():
        raise FileNotFoundError(
            f"{config_path} missing. Copy config/appium.example.json and edit capabilities."
        )

    config = AppiumConfig.from_file(config_path)
    if args.use_accessibility_dump:
        config.use_accessibility_dump = True

    llm = LLMClient(provider=args.provider, model=args.model)
    return AppiumBridge(config=config, llm_client=llm)


def main() -> None:
    args = parse_args()
    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO))
    bridge = build_bridge(args)

    try:
        plan = bridge.run_instruction(args.request)
        print(json.dumps([action.__dict__ for action in plan], indent=2, ensure_ascii=False))
    finally:
        bridge.disconnect()


if __name__ == "__main__":  # pragma: no cover
    main()
