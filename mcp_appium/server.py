#!/usr/bin/env python3
"""MCP Server for Appium natural language automation."""

from __future__ import annotations

import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import Any

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from mcp_appium.bridge import AppiumBridge
from mcp_appium.config import AppiumConfig
from mcp_appium.llm_client import LLMClient
from mcp_appium.appium_manager import AppiumServerManager
from mcp_appium.device_manager import detect_android_devices, get_first_available_device, get_device_info

logger = logging.getLogger(__name__)

# Global instances
bridge: AppiumBridge | None = None
appium_manager: AppiumServerManager | None = None
config_path = Path(__file__).parent.parent / "config" / "appium.json"


def get_bridge() -> AppiumBridge:
    """Get or create the Appium bridge instance."""
    global bridge
    if bridge is None:
        if not config_path.exists():
            raise FileNotFoundError(
                f"Config file not found: {config_path}. "
                "Copy config/appium.example.json to config/appium.json"
            )
        config = AppiumConfig.from_file(config_path)
        # Use mock provider by default (no API key needed)
        llm = LLMClient(provider="mock", model="mock")
        bridge = AppiumBridge(config=config, llm_client=llm)
    return bridge


async def main():
    """Run the MCP server."""
    server = Server("mcp-appium")

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        """List available Appium automation tools."""
        return [
            Tool(
                name="setup_appium_connection",
                description=(
                    "Automatically setup Appium server and connect to device. "
                    "This will: 1) Start Appium server if not running, "
                    "2) Auto-detect connected Android devices using adb, "
                    "3) Create/update configuration with detected device, "
                    "4) Connect to the device. "
                    "Use this as the first step to start automating a mobile device."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "port": {
                            "type": "integer",
                            "description": "Appium server port (default: 4723)",
                        },
                    },
                },
            ),
            Tool(
                name="list_devices",
                description=(
                    "List all connected Android devices detected by adb. "
                    "Shows device UDID, status, and model information. "
                    "Use this to see available devices before setup."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {},
                },
            ),
            Tool(
                name="start_appium_server",
                description=(
                    "Start the Appium server manually. "
                    "The server will run on the specified port (default: 4723). "
                    "Use this if you want to start the server separately from device setup."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "port": {
                            "type": "integer",
                            "description": "Appium server port (default: 4723)",
                        },
                    },
                },
            ),
            Tool(
                name="stop_appium_server",
                description=(
                    "Stop the running Appium server. "
                    "Use this to clean up after testing."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {},
                },
            ),
            Tool(
                name="get_screen_elements",
                description=(
                    "Get all UI elements currently visible on the mobile device screen. "
                    "Returns a list of elements with their text, content-desc, resource-id, and bounds. "
                    "Use this to analyze what's on screen before deciding what action to take."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {},
                },
            ),
            Tool(
                name="execute_action",
                description=(
                    "Execute a specific Appium action on the mobile device. "
                    "Actions: tap (click element), input_text (type text), swipe (scroll/swipe), "
                    "long_press (long press element), back (press back button), "
                    "hide_keyboard (hide on-screen keyboard), "
                    "scroll_down (scroll down), scroll_up (scroll up)"
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "action": {
                            "type": "string",
                            "enum": ["tap", "input_text", "swipe", "long_press", "back", "hide_keyboard", "scroll_down", "scroll_up"],
                            "description": "The type of action to perform",
                        },
                        "text": {
                            "type": "string",
                            "description": "For tap/long_press: text of element to find. For input_text: text to type",
                        },
                        "content_desc": {
                            "type": "string",
                            "description": "Content description of element to find (alternative to text)",
                        },
                        "resource_id": {
                            "type": "string",
                            "description": "Resource ID of element to find (alternative to text)",
                        },
                        "x": {
                            "type": "integer",
                            "description": "X coordinate for tap/long_press (if element not found by text/id)",
                        },
                        "y": {
                            "type": "integer",
                            "description": "Y coordinate for tap/long_press (if element not found by text/id)",
                        },
                        "duration": {
                            "type": "integer",
                            "description": "Duration in milliseconds for long_press (default: 1000)",
                        },
                    },
                    "required": ["action"],
                },
            ),
            Tool(
                name="run_test_scenario",
                description=(
                    "Run an automated test scenario based on natural language description. "
                    "The AI will analyze the screen, create a test plan, and execute it automatically. "
                    "Use this for complex multi-step test scenarios. "
                    "Example: 'Test the login flow with valid credentials', "
                    "'Navigate to settings and verify user profile information', "
                    "'Add an item to cart and proceed to checkout'"
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "scenario": {
                            "type": "string",
                            "description": "Natural language description of the test scenario to execute",
                        },
                        "max_steps": {
                            "type": "integer",
                            "description": "Maximum number of steps to execute (default: 10)",
                        },
                    },
                    "required": ["scenario"],
                },
            ),
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: Any) -> list[TextContent]:
        """Execute Appium automation tool."""
        global bridge, appium_manager

        try:
            if name == "setup_appium_connection":
                port = arguments.get("port", 4723)

                def setup():
                    global appium_manager, bridge

                    # Step 1: Start Appium server
                    if appium_manager is None:
                        appium_manager = AppiumServerManager(port=port, log_file="appium.log")

                    if not appium_manager.is_running():
                        logger.info("Starting Appium server...")
                        if not appium_manager.start(timeout=30):
                            raise RuntimeError("Failed to start Appium server")

                    # Step 2: Detect devices
                    logger.info("Detecting connected devices...")
                    device = get_first_available_device()
                    if not device:
                        raise RuntimeError(
                            "No Android devices found. Please ensure:\n"
                            "1. Device is connected via USB or emulator is running\n"
                            "2. USB debugging is enabled\n"
                            "3. Run 'adb devices' to verify connection"
                        )

                    # Get detailed device info
                    device_details = get_device_info(device.udid)

                    # Step 3: Create/update config
                    config_data = {
                        "server_url": appium_manager.server_url,
                        "capabilities": {
                            "platformName": "Android",
                            "automationName": "UiAutomator2",
                            "deviceName": device_details["model"],
                            "udid": device.udid,
                            "noReset": True,
                            "dontStopAppOnReset": True,
                            "skipDeviceInitialization": False,
                            "skipServerInstallation": False,
                            "newCommandTimeout": 300,
                        },
                        "adb_binary": "adb",
                        "use_accessibility_dump": False,
                    }

                    # Write config
                    config_path.parent.mkdir(parents=True, exist_ok=True)
                    config_path.write_text(json.dumps(config_data, indent=2))

                    # Step 4: Create bridge and connect
                    config = AppiumConfig.from_file(config_path)
                    llm = LLMClient(provider="mock", model="mock")
                    bridge = AppiumBridge(config=config, llm_client=llm)
                    bridge.connect()

                    return {
                        "server_url": appium_manager.server_url,
                        "device": device_details,
                        "config_path": str(config_path),
                    }

                result = await asyncio.to_thread(setup)

                response = f"""✅ Appium Setup Complete!

🚀 Server: {result['server_url']}
📱 Device: {result['device']['manufacturer']} {result['device']['model']} (Android {result['device']['android_version']})
🆔 UDID: {result['device']['udid']}
⚙️  Config: {result['config_path']}

You can now use get_screen_elements, execute_action, and other tools to automate the device!
"""
                return [TextContent(type="text", text=response)]

            elif name == "list_devices":
                def list_devs():
                    devices = detect_android_devices()
                    if not devices:
                        return {"devices": [], "count": 0}

                    device_list = []
                    for dev in devices:
                        dev_dict = dev.to_dict()
                        if dev.status == "device":
                            # Get detailed info for online devices
                            details = get_device_info(dev.udid)
                            dev_dict.update(details)
                        device_list.append(dev_dict)

                    return {"devices": device_list, "count": len(device_list)}

                result = await asyncio.to_thread(list_devs)

                if result["count"] == 0:
                    response = """📱 No Android devices found.

Please ensure:
1. Device is connected via USB or emulator is running
2. USB debugging is enabled on the device
3. Run 'adb devices' in terminal to verify
"""
                else:
                    response = f"""📱 Found {result['count']} device(s):

{json.dumps(result['devices'], indent=2, ensure_ascii=False)}
"""
                return [TextContent(type="text", text=response)]

            elif name == "start_appium_server":
                port = arguments.get("port", 4723)

                def start():
                    global appium_manager

                    if appium_manager is None:
                        appium_manager = AppiumServerManager(port=port, log_file="appium.log")

                    if appium_manager.is_running():
                        return {"status": "already_running", "url": appium_manager.server_url}

                    if appium_manager.start(timeout=30):
                        return {"status": "started", "url": appium_manager.server_url}
                    else:
                        raise RuntimeError("Failed to start Appium server")

                result = await asyncio.to_thread(start)

                if result["status"] == "already_running":
                    response = f"ℹ️  Appium server already running at {result['url']}"
                else:
                    response = f"✅ Appium server started at {result['url']}\n📝 Logs: appium.log"

                return [TextContent(type="text", text=response)]

            elif name == "stop_appium_server":
                def stop():
                    global appium_manager

                    if appium_manager is None or not appium_manager.is_running():
                        return {"status": "not_running"}

                    appium_manager.stop()
                    return {"status": "stopped"}

                result = await asyncio.to_thread(stop)

                if result["status"] == "not_running":
                    response = "ℹ️  Appium server is not running"
                else:
                    response = "✅ Appium server stopped"

                return [TextContent(type="text", text=response)]

            elif name == "get_screen_elements":
                # Get or create bridge
                appium_bridge = get_bridge()

                # Connect and collect screen elements
                def collect():
                    appium_bridge.connect()
                    return appium_bridge.collect_nodes()

                nodes = await asyncio.to_thread(collect)

                # Format elements as JSON
                elements = []
                for i, node in enumerate(nodes, 1):
                    elements.append({
                        "index": i,
                        "text": node.text,
                        "content_desc": node.content_desc,
                        "resource_id": node.resource_id,
                        "bounds": node.bounds,
                        "class_name": node.class_name,
                    })

                result = f"""📱 Screen Elements ({len(elements)} found):

{json.dumps(elements, indent=2, ensure_ascii=False)}

Use execute_action to interact with these elements.
"""
                return [TextContent(type="text", text=result)]

            elif name == "execute_action":
                action_type = arguments.get("action")
                if not action_type:
                    raise ValueError("action is required")

                appium_bridge = get_bridge()
                appium_bridge.connect()

                def execute():
                    from appium.webdriver.common.appiumby import AppiumBy
                    from selenium.webdriver.common.actions.action_builder import ActionBuilder
                    from selenium.webdriver.common.actions.pointer_input import PointerInput
                    from selenium.webdriver.common.actions import interaction

                    driver = appium_bridge.driver

                    if action_type == "tap":
                        # Try to find element by text, content-desc, or resource-id
                        element = None

                        if arguments.get("text"):
                            try:
                                element = driver.find_element(AppiumBy.XPATH, f"//*[@text='{arguments['text']}']")
                            except:
                                pass

                        if not element and arguments.get("content_desc"):
                            try:
                                element = driver.find_element(AppiumBy.XPATH, f"//*[@content-desc='{arguments['content_desc']}']")
                            except:
                                pass

                        if not element and arguments.get("resource_id"):
                            try:
                                element = driver.find_element(AppiumBy.ID, arguments["resource_id"])
                            except:
                                pass

                        if element:
                            element.click()
                            return f"✅ Tapped element: {arguments.get('text') or arguments.get('content_desc') or arguments.get('resource_id')}"
                        elif arguments.get("x") and arguments.get("y"):
                            # Tap by coordinates
                            actions = ActionBuilder(driver, mouse=PointerInput(interaction.POINTER_TOUCH, "touch"))
                            actions.pointer_action.move_to_location(arguments["x"], arguments["y"])
                            actions.pointer_action.pointer_down()
                            actions.pointer_action.pointer_up()
                            actions.perform()
                            return f"✅ Tapped at coordinates ({arguments['x']}, {arguments['y']})"
                        else:
                            raise RuntimeError("Element not found and no coordinates provided")

                    elif action_type == "input_text":
                        import time
                        element = None
                        text_to_type = arguments.get("text", "")

                        # Try to find element by resource_id or content_desc
                        if arguments.get("resource_id"):
                            try:
                                element = driver.find_element(AppiumBy.ID, arguments["resource_id"])
                            except:
                                pass
                        elif arguments.get("content_desc"):
                            try:
                                element = driver.find_element(AppiumBy.XPATH, f"//*[@content-desc='{arguments['content_desc']}']")
                            except:
                                pass

                        # If no element found, try to use the currently focused element
                        if not element:
                            try:
                                element = driver.switch_to.active_element
                                logger.info("Using active element for input")
                            except Exception as e:
                                logger.debug(f"Could not get active element: {e}")

                        # If still no element, try to find first EditText
                        if not element:
                            try:
                                element = driver.find_element(AppiumBy.CLASS_NAME, "android.widget.EditText")
                                logger.info("Using first EditText as fallback")
                            except:
                                pass

                        if element and text_to_type:
                            element.clear()
                            time.sleep(0.2)  # Small delay after clear
                            element.send_keys(text_to_type)
                            time.sleep(0.3)  # Small delay after sending keys
                            # Auto-hide keyboard
                            try:
                                driver.hide_keyboard()
                            except:
                                pass  # Keyboard might not be shown
                            return f"✅ Entered text: {text_to_type}"
                        else:
                            raise RuntimeError("Could not find input element")

                    elif action_type == "swipe":
                        # Simple swipe implementation
                        driver.swipe(500, 1000, 500, 300, 400)
                        return "✅ Swiped"

                    elif action_type == "long_press":
                        # Long press implementation
                        element = None
                        duration = arguments.get("duration", 1000)

                        if arguments.get("text"):
                            try:
                                element = driver.find_element(AppiumBy.XPATH, f"//*[@text='{arguments['text']}']")
                            except:
                                pass

                        if not element and arguments.get("content_desc"):
                            try:
                                element = driver.find_element(AppiumBy.XPATH, f"//*[@content-desc='{arguments['content_desc']}']")
                            except:
                                pass

                        if not element and arguments.get("resource_id"):
                            try:
                                element = driver.find_element(AppiumBy.ID, arguments["resource_id"])
                            except:
                                pass

                        if element:
                            location = element.location
                            size = element.size
                            x = location['x'] + size['width'] // 2
                            y = location['y'] + size['height'] // 2
                        elif arguments.get("x") and arguments.get("y"):
                            x = arguments["x"]
                            y = arguments["y"]
                        else:
                            raise RuntimeError("Element not found and no coordinates provided")

                        # W3C Actions API for long press
                        actions = ActionBuilder(driver, mouse=PointerInput(interaction.POINTER_TOUCH, "touch"))
                        actions.pointer_action.move_to_location(x, y)
                        actions.pointer_action.pointer_down()
                        actions.pointer_action.pause(duration / 1000.0)
                        actions.pointer_action.pointer_up()
                        actions.perform()
                        return f"✅ Long pressed ({duration}ms): {arguments.get('text') or arguments.get('content_desc') or f'({x}, {y})'}"

                    elif action_type == "back":
                        driver.back()
                        return "✅ Pressed back button"

                    elif action_type == "hide_keyboard":
                        try:
                            driver.hide_keyboard()
                            return "✅ Keyboard hidden"
                        except Exception as e:
                            # Keyboard might not be shown, which is fine
                            return f"ℹ️ Keyboard hide attempted (may already be hidden): {str(e)}"

                    elif action_type == "scroll_down":
                        size = driver.get_window_size()
                        width = size['width']
                        height = size['height']
                        start_x = width // 2
                        start_y = int(height * 0.8)
                        end_x = width // 2
                        end_y = int(height * 0.2)

                        actions = ActionBuilder(driver, mouse=PointerInput(interaction.POINTER_TOUCH, "touch"))
                        actions.pointer_action.move_to_location(start_x, start_y)
                        actions.pointer_action.pointer_down()
                        actions.pointer_action.pause(0.3)
                        actions.pointer_action.move_to_location(end_x, end_y)
                        actions.pointer_action.pointer_up()
                        actions.perform()
                        return "✅ Scrolled down"

                    elif action_type == "scroll_up":
                        size = driver.get_window_size()
                        width = size['width']
                        height = size['height']
                        start_x = width // 2
                        start_y = int(height * 0.2)
                        end_x = width // 2
                        end_y = int(height * 0.8)

                        actions = ActionBuilder(driver, mouse=PointerInput(interaction.POINTER_TOUCH, "touch"))
                        actions.pointer_action.move_to_location(start_x, start_y)
                        actions.pointer_action.pointer_down()
                        actions.pointer_action.pause(0.3)
                        actions.pointer_action.move_to_location(end_x, end_y)
                        actions.pointer_action.pointer_up()
                        actions.perform()
                        return "✅ Scrolled up"

                    else:
                        raise ValueError(f"Unknown action: {action_type}")

                result = await asyncio.to_thread(execute)
                return [TextContent(type="text", text=result)]

            elif name == "run_test_scenario":
                scenario = arguments.get("scenario")
                if not scenario:
                    raise ValueError("scenario is required")

                max_steps = arguments.get("max_steps", 10)

                appium_bridge = get_bridge()

                def run_scenario():
                    try:
                        executed_actions = appium_bridge.run_instruction(scenario, max_turns=max_steps)

                        # Format the result
                        result_lines = [f"🤖 Test Scenario: {scenario}", "", "Executed actions:"]
                        for i, action in enumerate(executed_actions, 1):
                            result_lines.append(f"  {i}. {action.describe()}")

                        result_lines.append("")
                        result_lines.append(f"✅ Completed {len(executed_actions)} actions")

                        return "\n".join(result_lines)
                    except Exception as exc:
                        logger.exception("Scenario execution failed")
                        return f"❌ Scenario failed: {str(exc)}"

                result = await asyncio.to_thread(run_scenario)
                return [TextContent(type="text", text=result)]

            else:
                raise ValueError(f"Unknown tool: {name}")

        except Exception as e:
            logger.exception(f"Error in {name}")
            error_msg = f"""❌ Error in {name}:

{str(e)}

Make sure:
1. Appium server is running (appium --base-path /)
2. Device/emulator is connected (adb devices)
3. Config file exists at {config_path}
"""
            return [TextContent(type="text", text=error_msg)]

    # Run the server
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
