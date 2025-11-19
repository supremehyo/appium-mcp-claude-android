from __future__ import annotations

import logging
import subprocess
import time
from typing import List, Sequence

from appium import webdriver
from appium.options.android import UiAutomator2Options
from appium.options.ios import XCUITestOptions
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.common.actions import interaction
from selenium.webdriver.common.actions.action_builder import ActionBuilder
from selenium.webdriver.common.actions.pointer_input import PointerInput

from .config import AppiumConfig
from .llm_client import LLMClient
from .node_parser import NodeParser, NodeSnapshot
from .prompt import PromptBuilder
from .action_types import PlannedAction

logger = logging.getLogger(__name__)


class AppiumBridge:
    """Coordinates Appium, adb dumps and the LLM planner."""

    def __init__(
        self,
        config: AppiumConfig,
        llm_client: LLMClient,
        prompt_builder: PromptBuilder | None = None,
    ) -> None:
        self.config = config
        self.llm = llm_client
        self.prompt_builder = prompt_builder or PromptBuilder(config.to_prompt_payload())
        self.driver: webdriver.Remote | None = None
        self.current_nodes: List[NodeSnapshot] = []

    # Connection --------------------------------------------------------------
    def connect(self, max_retries: int = 3, retry_delay: int = 2) -> None:
        if self.driver:
            try:
                # Test if the existing connection is still valid using session_id
                # This is more reliable than current_activity which requires an active app
                _ = self.driver.session_id
                logger.info("Existing connection is valid (session: %s)", self.driver.session_id)
                return
            except Exception as e:
                # Connection is stale, disconnect and reconnect
                logger.warning("Existing driver connection is stale (%s), reconnecting...", str(e))
                try:
                    self.driver.quit()
                except:
                    pass
                self.driver = None

        logger.info("Connecting to Appium server at %s", self.config.server_url)

        # Convert capabilities dict to Options object
        caps = self.config.capabilities
        platform = caps.get("platformName", "").lower()

        if platform == "android":
            options = UiAutomator2Options()
        elif platform == "ios":
            options = XCUITestOptions()
        else:
            raise ValueError(f"Unsupported platform: {platform}")

        # Load capabilities into options
        options.load_capabilities(caps)

        # Retry logic for connection stability
        last_error = None
        for attempt in range(max_retries):
            try:
                logger.info("Connection attempt %d/%d", attempt + 1, max_retries)
                self.driver = webdriver.Remote(self.config.server_url, options=options)
                logger.info("Successfully connected to device (session: %s)", self.driver.session_id)
                return
            except Exception as e:
                last_error = e
                logger.warning("Connection attempt %d failed: %s", attempt + 1, str(e))
                if attempt < max_retries - 1:
                    logger.info("Retrying in %d seconds...", retry_delay)
                    time.sleep(retry_delay)
                else:
                    logger.error("All %d connection attempts failed", max_retries)

        # If all retries failed, raise the last error
        raise RuntimeError(f"Failed to connect after {max_retries} attempts: {last_error}") from last_error

    def disconnect(self) -> None:
        if self.driver:
            logger.info("Closing Appium session")
            self.driver.quit()
            self.driver = None

    # Data collection ---------------------------------------------------------
    def collect_nodes(self) -> List[NodeSnapshot]:
        if self.config.use_accessibility_dump:
            dump = self._collect_accessibility_dump()
            nodes = NodeParser.parse_accessibility_dump(dump)
            if nodes:
                return nodes
            logger.warning("Accessibility dump empty, falling back to Appium source")

        if not self.driver:
            raise RuntimeError("Driver not connected")

        xml = self.driver.page_source
        return NodeParser.parse_xml(xml)

    def _collect_accessibility_dump(self) -> str:
        try:
            result = subprocess.run(
                [self.config.adb_binary, "shell", "dumpsys", "accessibility"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False,
                timeout=10,  # Add timeout to prevent hanging
            )
        except FileNotFoundError as exc:  # pragma: no cover - depends on adb
            logger.error("ADB binary not found: %s", exc)
            return ""
        except subprocess.TimeoutExpired:
            logger.error("adb dumpsys timed out after 10 seconds")
            return ""

        if result.returncode != 0:
            logger.error("adb dumpsys failed: %s", result.stderr.strip())
            return ""
        return result.stdout

    # Planning/execution ------------------------------------------------------
    def run_instruction(self, request: str, max_turns: int = 4) -> List[PlannedAction]:
        self.connect()
        executed_actions: List[PlannedAction] = []
        self.current_nodes = self.collect_nodes()
        history: List[str] = []

        for turn in range(max_turns):
            logger.info("Planning turn %d", turn + 1)
            history_text = "\n".join(reversed(history[-6:]))
            prompt = self.prompt_builder.build(request, self.current_nodes, history_text)
            plan = self.llm.plan_actions(
                prompt,
                fallback_nodes=[
                    {**node.as_dict(), "index": idx + 1} for idx, node in enumerate(self.current_nodes)
                ],
            )
            logger.info("LLM produced %d actions", len(plan.actions))
            exec_log = self._execute_plan(plan.actions)
            history.extend(exec_log)
            executed_actions.extend(plan.actions)

            if not plan.request_refresh:
                logger.info("Planner requested stop")
                break

            self.current_nodes = self.collect_nodes()

        return executed_actions

    def _execute_plan(self, plan: Sequence[PlannedAction]) -> List[str]:
        if not self.driver:
            raise RuntimeError("Driver not connected")

        logs: List[str] = []

        for action in plan:
            logger.info("Executing %s", action.describe())
            try:
                if action.name == "tap":
                    self._tap(action)
                elif action.name == "input_text":
                    self._input(action)
                elif action.name == "wait":
                    duration = float(action.value or 1.0)
                    time.sleep(duration)
                elif action.name == "assert_text":
                    self._assert_text(action)
                elif action.name == "swipe":
                    self._swipe(action)
                elif action.name == "long_press":
                    self._long_press(action)
                elif action.name == "back":
                    self._back()
                elif action.name == "hide_keyboard":
                    self._hide_keyboard()
                elif action.name == "scroll_down":
                    self._scroll_down()
                elif action.name == "scroll_up":
                    self._scroll_up()
                else:
                    logger.warning("Skipping unsupported action: %s", action.name)
                    logs.append(f"skip:{action.describe()}")
                    continue
                logs.append(f"ok:{action.describe()}")
            except Exception as exc:
                logger.exception("Action failed: %s", exc)
                logs.append(f"error:{action.describe()} reason={exc}")
                raise

        return logs

    # Action helpers ----------------------------------------------------------
    def _tap(self, action: PlannedAction) -> None:
        element = self._resolve_element(action)
        if element:
            element.click()
        else:
            coords = self._parse_coordinates(action.value)
            if not coords and action.metadata:
                coords = self._parse_coordinates(action.metadata.get("fallback_coordinates"))
            if coords and self.driver:
                # W3C Actions API for tap
                actions = ActionBuilder(self.driver, mouse=PointerInput(interaction.POINTER_TOUCH, "touch"))
                actions.pointer_action.move_to_location(coords[0], coords[1])
                actions.pointer_action.pointer_down()
                actions.pointer_action.pointer_up()
                actions.perform()
            else:
                logger.error("Tap failed: no locator or coordinates available")

    def _input(self, action: PlannedAction) -> None:
        element = self._resolve_element(action, wait=True)

        # If element not found, try to find the currently focused EditText
        if not element and self.driver:
            try:
                # Try to find active/focused element
                element = self.driver.switch_to.active_element
                logger.info("Using active element for input")
            except Exception as e:
                logger.debug(f"Could not get active element: {e}")

                # Try to find any EditText as fallback
                try:
                    element = self.driver.find_element(AppiumBy.CLASS_NAME, "android.widget.EditText")
                    logger.info("Using first EditText as fallback")
                except Exception:
                    pass

        if not element:
            raise RuntimeError("Unable to resolve element for input_text")

        element.clear()
        if action.value:
            element.send_keys(action.value)

        # Auto-hide keyboard after input (unless explicitly disabled in metadata)
        auto_hide = action.metadata.get("auto_hide_keyboard", True) if action.metadata else True
        if auto_hide:
            time.sleep(0.3)  # Small delay to ensure input is complete
            self._hide_keyboard()

    def _assert_text(self, action: PlannedAction) -> None:
        element = self._resolve_element(action, wait=True)
        if not element:
            raise AssertionError("assert_text failed: element missing")

        expected = (action.value or "").strip()
        actual = (element.text or "").strip()
        if expected not in actual:
            raise AssertionError(f"Expected '{expected}' in '{actual}'")

    def _swipe(self, action: PlannedAction) -> None:
        if not self.driver:
            return
        start = self._parse_coordinates(action.value)
        end = self._parse_coordinates(action.metadata.get("end")) if action.metadata else None
        duration_ms = int(action.metadata.get("duration_ms", 400)) if action.metadata else 400
        if not start or not end:
            logger.error("Swipe requires start and end coordinates")
            return

        # W3C Actions API for swipe
        actions = ActionBuilder(self.driver, mouse=PointerInput(interaction.POINTER_TOUCH, "touch"))
        actions.pointer_action.move_to_location(start[0], start[1])
        actions.pointer_action.pointer_down()
        actions.pointer_action.pause(duration_ms / 1000.0)
        actions.pointer_action.move_to_location(end[0], end[1])
        actions.pointer_action.pointer_up()
        actions.perform()

    def _long_press(self, action: PlannedAction) -> None:
        """Long press on an element or coordinates."""
        if not self.driver:
            return

        element = self._resolve_element(action)
        duration_ms = int(action.metadata.get("duration_ms", 1000)) if action.metadata else 1000

        if element:
            # Long press on element
            location = element.location
            size = element.size
            x = location['x'] + size['width'] // 2
            y = location['y'] + size['height'] // 2
        else:
            # Long press by coordinates
            coords = self._parse_coordinates(action.value)
            if not coords and action.metadata:
                coords = self._parse_coordinates(action.metadata.get("fallback_coordinates"))
            if not coords:
                logger.error("Long press failed: no element or coordinates available")
                return
            x, y = coords

        # W3C Actions API for long press
        actions = ActionBuilder(self.driver, mouse=PointerInput(interaction.POINTER_TOUCH, "touch"))
        actions.pointer_action.move_to_location(x, y)
        actions.pointer_action.pointer_down()
        actions.pointer_action.pause(duration_ms / 1000.0)
        actions.pointer_action.pointer_up()
        actions.perform()

    def _back(self) -> None:
        """Press the back button."""
        if not self.driver:
            return
        self.driver.back()

    def _hide_keyboard(self) -> None:
        """Hide the on-screen keyboard."""
        if not self.driver:
            return
        try:
            # Try to hide keyboard - works on both Android and iOS
            self.driver.hide_keyboard()
            logger.info("Keyboard hidden successfully")
        except Exception as e:
            # If hide_keyboard fails, it might mean keyboard is not shown
            # or the method is not supported - this is not critical
            logger.debug(f"hide_keyboard failed (this is normal if keyboard is not shown): {e}")

    def _is_keyboard_shown(self) -> bool:
        """Check if keyboard is currently shown."""
        if not self.driver:
            return False
        try:
            # Try to get keyboard status
            return self.driver.is_keyboard_shown()
        except Exception as e:
            # If method not supported, assume keyboard might be shown
            logger.debug(f"is_keyboard_shown not supported: {e}")
            return False

    def _scroll_down(self) -> None:
        """Scroll down on the screen."""
        if not self.driver:
            return
        # Get screen size
        size = self.driver.get_window_size()
        width = size['width']
        height = size['height']

        # Scroll from bottom to top (swipe up)
        start_x = width // 2
        start_y = int(height * 0.8)
        end_x = width // 2
        end_y = int(height * 0.2)

        actions = ActionBuilder(self.driver, mouse=PointerInput(interaction.POINTER_TOUCH, "touch"))
        actions.pointer_action.move_to_location(start_x, start_y)
        actions.pointer_action.pointer_down()
        actions.pointer_action.pause(0.3)
        actions.pointer_action.move_to_location(end_x, end_y)
        actions.pointer_action.pointer_up()
        actions.perform()

    def _scroll_up(self) -> None:
        """Scroll up on the screen."""
        if not self.driver:
            return
        # Get screen size
        size = self.driver.get_window_size()
        width = size['width']
        height = size['height']

        # Scroll from top to bottom (swipe down)
        start_x = width // 2
        start_y = int(height * 0.2)
        end_x = width // 2
        end_y = int(height * 0.8)

        actions = ActionBuilder(self.driver, mouse=PointerInput(interaction.POINTER_TOUCH, "touch"))
        actions.pointer_action.move_to_location(start_x, start_y)
        actions.pointer_action.pointer_down()
        actions.pointer_action.pause(0.3)
        actions.pointer_action.move_to_location(end_x, end_y)
        actions.pointer_action.pointer_up()
        actions.perform()

    # Locator helpers ---------------------------------------------------------
    def _resolve_element(self, action: PlannedAction, wait: bool = False):
        if not self.driver:
            return None
        locator = action.locator or {}
        strategy = locator.get("strategy")
        value = locator.get("value")

        if strategy == "coordinates":
            return None

        if strategy == "node_index":
            node = self._node_from_index(value)
            if not node:
                return None
            inferred = node.preferred_locator()
            if inferred:
                element = self._find_element(inferred["strategy"], inferred["value"])
                # If element not found and keyboard is shown, try hiding keyboard and retry
                if not element and self._is_keyboard_shown():
                    logger.info("Element not found, hiding keyboard and retrying...")
                    self._hide_keyboard()
                    time.sleep(0.5)  # Wait for keyboard to hide
                    element = self._find_element(inferred["strategy"], inferred["value"])
                return element
            coords = _center_of_bounds(node.bounds)
            if coords:
                action.metadata.setdefault("fallback_coordinates", coords)
            return None

        if strategy == "text":
            xpath = f"//*[@text='{value}' or @content-desc='{value}']"
            try:
                element = self.driver.find_element(AppiumBy.XPATH, xpath)
                return element
            except:
                # If element not found and keyboard is shown, try hiding keyboard and retry
                if self._is_keyboard_shown():
                    logger.info("Element not found, hiding keyboard and retrying...")
                    self._hide_keyboard()
                    time.sleep(0.5)  # Wait for keyboard to hide
                    try:
                        return self.driver.find_element(AppiumBy.XPATH, xpath)
                    except:
                        pass
                return None

        element = self._find_element(strategy, value)
        # If element not found and keyboard is shown, try hiding keyboard and retry
        if not element and self._is_keyboard_shown():
            logger.info("Element not found, hiding keyboard and retrying...")
            self._hide_keyboard()
            time.sleep(0.5)  # Wait for keyboard to hide
            element = self._find_element(strategy, value)
        return element

    def _find_element(self, strategy: str | None, value: str | None):
        if not self.driver or not strategy or not value:
            return None

        strategy_map = {
            "id": AppiumBy.ID,
            "accessibility_id": AppiumBy.ACCESSIBILITY_ID,
            "xpath": AppiumBy.XPATH,
            "android_uiautomator": AppiumBy.ANDROID_UIAUTOMATOR,
            "ios_predicate": AppiumBy.IOS_PREDICATE,
        }

        by = strategy_map.get(strategy)
        if not by:
            return None
        return self.driver.find_element(by, value)

    def _node_from_index(self, value) -> NodeSnapshot | None:
        if not value:
            return None
        try:
            index = int(value)
        except (TypeError, ValueError):
            return None
        if index <= 0 or index > len(self.current_nodes):
            return None
        return self.current_nodes[index - 1]

    @staticmethod
    def _parse_coordinates(raw):
        if not raw:
            return None
        if isinstance(raw, (list, tuple)) and len(raw) >= 2:
            return int(raw[0]), int(raw[1])
        try:
            parts = [int(part.strip()) for part in raw.replace(",", " ").split()]
            if len(parts) >= 2:
                return parts[0], parts[1]
        except ValueError:
            return None
        return None


def _center_of_bounds(bounds):
    x1, y1, x2, y2 = bounds
    if x1 == x2 == y1 == y2 == 0:
        return None
    return (int((x1 + x2) / 2), int((y1 + y2) / 2))
