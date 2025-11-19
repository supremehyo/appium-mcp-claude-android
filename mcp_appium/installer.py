#!/usr/bin/env python3
"""Automated installer for mcp-appium MCP server."""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


def get_claude_code_config_path() -> Path:
    """Get the path to Claude Code's MCP configuration file."""
    home = Path.home()

    if sys.platform == "darwin":  # macOS
        return home / ".config" / "claude-code" / "config.json"
    elif sys.platform == "win32":  # Windows
        appdata = Path(os.environ.get("APPDATA", home / "AppData" / "Roaming"))
        return appdata / "claude-code" / "config.json"
    else:  # Linux
        return home / ".config" / "claude-code" / "config.json"


def register_with_claude_code():
    """Register mcp-appium with Claude Code using claude mcp add command."""
    try:
        # Get Python executable path
        python_path = sys.executable

        # Check if already registered
        check_cmd = ["claude", "mcp", "list"]
        try:
            result = subprocess.run(
                check_cmd,
                capture_output=True,
                text=True,
                check=False,
            )
            if "appium" in result.stdout:
                print("ℹ️  MCP server 'appium' is already registered.")
                print("\nIf you want to update it, run:")
                print("  claude mcp remove appium")
                print("  mcp-appium-install")
                return True
        except:
            pass  # Ignore errors from list command

        # Register the MCP server using claude mcp add
        cmd = [
            "claude",
            "mcp",
            "add",
            "--transport", "stdio",
            "appium",
            "--",
            python_path,
            "-m",
            "mcp_appium.server",
        ]

        print(f"Registering MCP server with Claude Code...")
        print(f"Command: {' '.join(cmd)}")

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode == 0:
            print("✅ MCP server registered successfully!")
            print("\nYou can now use the following MCP tools in Claude Code:")
            print("  - setup_appium_connection: Auto-setup Appium and connect to device")
            print("  - list_devices: List connected Android devices")
            print("  - start_appium_server: Start Appium server")
            print("  - stop_appium_server: Stop Appium server")
            print("  - get_screen_elements: Get current screen elements")
            print("  - execute_action: Execute mobile actions")
            print("  - run_test_scenario: Run automated test scenarios")
            return True
        else:
            # Check if error is "already exists"
            if "already exists" in result.stderr:
                print("ℹ️  MCP server 'appium' is already registered.")
                print("\nTo update, run:")
                print("  claude mcp remove appium")
                print("  mcp-appium-install")
                return True
            else:
                print(f"⚠️  Warning: Failed to register MCP server automatically")
                print(f"stderr: {result.stderr}")
                print("\nYou can register manually with:")
                print(f"  claude mcp add --transport stdio appium -- {python_path} -m mcp_appium.server")
                return True  # Still return True as installation itself succeeded

    except FileNotFoundError:
        print("⚠️  'claude' command not found.")
        print("Please ensure Claude Code CLI is installed and in your PATH.")
        print("\nYou can register manually later with:")
        print("  claude mcp add --transport stdio appium -- python3 -m mcp_appium.server")
        return True  # Still return True as installation itself succeeded
    except Exception as e:
        print(f"⚠️  Warning: Unexpected error during registration: {e}")
        print("\nYou can register manually with:")
        print("  claude mcp add --transport stdio appium -- python3 -m mcp_appium.server")
        return True  # Still return True as installation itself succeeded


def unregister_from_claude_code():
    """Unregister mcp-appium from Claude Code."""
    try:
        cmd = ["claude", "mcp", "remove", "appium"]

        print("Unregistering MCP server from Claude Code...")

        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True,
        )

        print("✅ MCP server unregistered successfully!")
        return True

    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to unregister MCP server: {e}")
        return False
    except FileNotFoundError:
        print("❌ 'claude' command not found.")
        return False


def check_requirements():
    """Check if required tools are installed."""
    checks = {
        "Python": sys.executable,
        "adb": None,
        "appium": None,
    }

    # Check adb
    try:
        result = subprocess.run(
            ["adb", "version"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            checks["adb"] = "✅ Installed"
        else:
            checks["adb"] = "❌ Not found"
    except FileNotFoundError:
        checks["adb"] = "❌ Not found"

    # Check appium
    try:
        result = subprocess.run(
            ["appium", "--version"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            checks["appium"] = f"✅ Installed ({result.stdout.strip()})"
        else:
            checks["appium"] = "❌ Not found"
    except FileNotFoundError:
        checks["appium"] = "❌ Not found"

    print("\n📋 Requirements Check:")
    print(f"  Python: ✅ {sys.executable}")
    print(f"  adb: {checks['adb']}")
    print(f"  appium: {checks['appium']}")

    if "❌" in checks["adb"]:
        print("\n⚠️  adb is not installed. Please install Android SDK Platform-Tools.")
        print("   Visit: https://developer.android.com/studio/releases/platform-tools")

    if "❌" in checks["appium"]:
        print("\n⚠️  Appium is not installed. Please install it with:")
        print("   npm install -g appium")
        print("   appium driver install uiautomator2")

    return "❌" not in checks["adb"] and "❌" not in checks["appium"]


def main():
    """Main installer function."""
    parser = argparse.ArgumentParser(
        description="Install and register mcp-appium with Claude Code"
    )
    parser.add_argument(
        "--uninstall",
        action="store_true",
        help="Unregister mcp-appium from Claude Code",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check requirements only",
    )

    args = parser.parse_args()

    print("=" * 60)
    print("MCP Appium Installer")
    print("=" * 60)

    if args.check:
        check_requirements()
        return

    if args.uninstall:
        if unregister_from_claude_code():
            print("\n✅ Uninstallation complete!")
        else:
            print("\n❌ Uninstallation failed!")
            sys.exit(1)
        return

    # Installation
    print("\n1. Checking requirements...")
    all_ok = check_requirements()

    if not all_ok:
        print("\n⚠️  Some requirements are missing. Please install them first.")
        response = input("\nContinue anyway? (y/N): ")
        if response.lower() != "y":
            print("Installation cancelled.")
            sys.exit(1)

    print("\n2. Registering MCP server with Claude Code...")
    if register_with_claude_code():
        print("\n" + "=" * 60)
        print("✅ Installation complete!")
        print("=" * 60)
        print("\n📝 Next steps:")
        print("  1. Restart Claude Code")
        print("  2. Connect an Android device or start an emulator")
        print("  3. In Claude Code, say: 'Setup Appium and connect to my device'")
        print("\n💡 Tip: Use 'list_devices' to see connected devices first")
    else:
        print("\n❌ Installation failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
