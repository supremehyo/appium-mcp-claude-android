#!/usr/bin/env python3
"""Automated installer for mcp-appium MCP server."""

import argparse
import json
import os
import subprocess
import sys
import shutil
import tempfile
import zipfile
from urllib.request import urlretrieve
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

        # Register the MCP server using claude mcp add with --global flag
        cmd = [
            "claude",
            "mcp",
            "add",
            "--global",
            "--transport", "stdio",
            "appium",
            "--",
            python_path,
            "-m",
            "mcp_appium.server",
        ]

        print(f"Registering MCP server globally with Claude Code...")
        print(f"Command: {' '.join(cmd)}")

        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True,
        )

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

    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to register MCP server: {e}")
        print(f"stderr: {e.stderr}")
        return False
    except FileNotFoundError:
        print("❌ 'claude' command not found.")
        print("Please ensure Claude Code CLI is installed and in your PATH.")
        return False


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


def _which(cmd: str) -> str | None:
    return shutil.which(cmd)


def _run(cmd: list[str], *, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, check=check, capture_output=True, text=True)


def _have_cmd(cmd: str) -> bool:
    return _which(cmd) is not None


def _is_root() -> bool:
    geteuid = getattr(os, "geteuid", None)
    return bool(geteuid and geteuid() == 0)


def _sudo_prefix() -> list[str]:
    if _is_root():
        return []
    if _have_cmd("sudo"):
        return ["sudo"]
    return []


def _install_nodejs_npm_linux(*, yes: bool) -> bool:
    pm_cmds: list[tuple[str, list[str]]] = []
    if _have_cmd("apt-get"):
        pm_cmds.append(("apt-get", ["apt-get"]))
    if _have_cmd("dnf"):
        pm_cmds.append(("dnf", ["dnf"]))
    if _have_cmd("yum"):
        pm_cmds.append(("yum", ["yum"]))
    if _have_cmd("pacman"):
        pm_cmds.append(("pacman", ["pacman"]))
    if _have_cmd("zypper"):
        pm_cmds.append(("zypper", ["zypper"]))
    if _have_cmd("apk"):
        pm_cmds.append(("apk", ["apk"]))

    if not pm_cmds:
        print("❌ Could not find a supported Linux package manager (apt/dnf/yum/pacman/zypper/apk).")
        return False

    pm_name, pm = pm_cmds[0]
    if not yes:
        response = input(f"Node.js/npm not found. Install via {pm_name}? (y/N): ").strip().lower()
        if response != "y":
            return False

    sudo = _sudo_prefix()
    try:
        if pm_name == "apt-get":
            _run([*sudo, *pm, "update"], check=True)
            _run([*sudo, *pm, "install", "-y", "nodejs", "npm"], check=True)
        elif pm_name in {"dnf", "yum"}:
            _run([*sudo, *pm, "install", "-y", "nodejs", "npm"], check=True)
        elif pm_name == "pacman":
            _run([*sudo, *pm, "-Sy", "--noconfirm", "nodejs", "npm"], check=True)
        elif pm_name == "zypper":
            _run([*sudo, *pm, "install", "-y", "nodejs", "npm"], check=True)
        elif pm_name == "apk":
            _run([*sudo, *pm, "add", "nodejs", "npm"], check=True)
        else:
            return False
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install Node.js/npm via {pm_name}: {e}")
        if e.stderr:
            print(e.stderr.strip())
        return False

    return _have_cmd("node") and _have_cmd("npm")


def _install_nodejs_npm_macos(*, yes: bool) -> bool:
    if not _have_cmd("brew"):
        print("❌ Homebrew not found. Please install Node.js from https://nodejs.org/ or install Homebrew.")
        return False

    if not yes:
        response = input("Node.js/npm not found. Install via Homebrew (brew install node)? (y/N): ").strip().lower()
        if response != "y":
            return False

    try:
        _run(["brew", "install", "node"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install Node.js via Homebrew: {e}")
        if e.stderr:
            print(e.stderr.strip())
        return False

    return _have_cmd("node") and _have_cmd("npm")


def _install_nodejs_npm_windows(*, yes: bool) -> bool:
    if _have_cmd("node") and _have_cmd("npm"):
        return True

    def _ensure_node_on_path() -> None:
        program_files = os.environ.get("ProgramFiles")
        program_files_x86 = os.environ.get("ProgramFiles(x86)")
        candidates: list[Path] = []
        for root in [program_files, program_files_x86]:
            if not root:
                continue
            candidates.append(Path(root) / "nodejs")
        for cand in candidates:
            if (cand / "node.exe").exists():
                _prepend_path(cand)
                break

    # Prefer winget when available (default on Windows 10/11).
    if _have_cmd("winget"):
        if not yes:
            response = input("Node.js/npm not found. Install via winget (OpenJS.NodeJS.LTS)? (y/N): ").strip().lower()
            if response != "y":
                return False
        try:
            _run(
                [
                    "winget",
                    "install",
                    "--id",
                    "OpenJS.NodeJS.LTS",
                    "-e",
                    "--silent",
                    "--disable-interactivity",
                    "--accept-package-agreements",
                    "--accept-source-agreements",
                ],
                check=True,
            )
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install Node.js via winget: {e}")
            if e.stderr:
                print(e.stderr.strip())
            return False

        _ensure_node_on_path()
        return _have_cmd("node") and _have_cmd("npm")

    # Fallback to Chocolatey if present.
    if _have_cmd("choco"):
        if not yes:
            response = input("Node.js/npm not found. Install via Chocolatey (nodejs-lts)? (y/N): ").strip().lower()
            if response != "y":
                return False
        try:
            _run(["choco", "install", "nodejs-lts", "-y"], check=True)
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install Node.js via Chocolatey: {e}")
            if e.stderr:
                print(e.stderr.strip())
            return False

        _ensure_node_on_path()
        return _have_cmd("node") and _have_cmd("npm")

    print("❌ Could not auto-install Node.js/npm on Windows (winget/choco not found).")
    print("   Install Node.js from https://nodejs.org/ then re-run with --install-appium.")
    return False


def install_nodejs_npm(*, yes: bool = False) -> bool:
    if _have_cmd("node") and _have_cmd("npm"):
        return True

    if sys.platform == "darwin":
        return _install_nodejs_npm_macos(yes=yes)
    if sys.platform == "win32":
        return _install_nodejs_npm_windows(yes=yes)
    if sys.platform.startswith("linux"):
        return _install_nodejs_npm_linux(yes=yes)

    print("❌ Automatic Node.js/npm installation is only supported on macOS/Linux/Windows.")
    return False


def _prepend_path(path: Path) -> None:
    current = os.environ.get("PATH", "")
    path_str = str(path)
    parts = current.split(os.pathsep) if current else []
    if parts and parts[0] == path_str:
        return
    if path_str in parts:
        parts.remove(path_str)
    os.environ["PATH"] = os.pathsep.join([path_str, *parts])


def _add_to_user_path_windows(path: Path) -> bool:
    try:
        import winreg
    except Exception:
        return False

    path_str = str(path)
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Environment", 0, winreg.KEY_READ) as key:
            try:
                current, _ = winreg.QueryValueEx(key, "Path")
            except FileNotFoundError:
                current = ""
    except OSError:
        current = ""

    current_parts = [p for p in str(current).split(os.pathsep) if p]
    if path_str in current_parts:
        return True

    new_value = os.pathsep.join([*current_parts, path_str]) if current_parts else path_str
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Environment", 0, winreg.KEY_SET_VALUE) as key:
            winreg.SetValueEx(key, "Path", 0, winreg.REG_EXPAND_SZ, new_value)
    except OSError:
        return False

    return True


def install_adb(*, yes: bool = False) -> bool:
    if _have_cmd("adb"):
        return True

    if sys.platform != "win32":
        print("❌ Automatic adb installation is currently supported only on Windows.")
        print("   Install Android SDK Platform-Tools: https://developer.android.com/studio/releases/platform-tools")
        return False

    if not yes:
        response = input("adb not found. Install Android Platform-Tools (download + unzip)? (y/N): ").strip().lower()
        if response != "y":
            return False

    platform_tools_url = "https://dl.google.com/android/repository/platform-tools-latest-windows.zip"
    local_appdata = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    target_root = local_appdata / "Android"
    target_root.mkdir(parents=True, exist_ok=True)

    zip_path = Path(tempfile.gettempdir()) / "platform-tools-latest-windows.zip"
    try:
        print(f"Downloading Platform-Tools: {platform_tools_url}")
        urlretrieve(platform_tools_url, str(zip_path))
    except Exception as e:
        print(f"❌ Failed to download Platform-Tools: {e}")
        return False

    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(target_root)
    except Exception as e:
        print(f"❌ Failed to extract Platform-Tools: {e}")
        return False

    adb_dir = target_root / "platform-tools"
    if not adb_dir.exists():
        print(f"❌ Extracted Platform-Tools not found at: {adb_dir}")
        return False

    _prepend_path(adb_dir)
    if not _add_to_user_path_windows(adb_dir):
        print("⚠️  Failed to persist PATH update; adb will work only in this session.")
    else:
        print("✅ Added Platform-Tools to user PATH (restart terminal/Claude Code to take effect).")

    return _have_cmd("adb")


def install_appium(*, yes: bool = False) -> bool:
    if _have_cmd("appium"):
        return True

    if not (_have_cmd("node") and _have_cmd("npm")):
        print("❌ Node.js/npm not found. Install them first (or run with --install-node).")
        return False

    if not yes:
        response = input("Appium not found. Install globally (npm install -g appium)? (y/N): ").strip().lower()
        if response != "y":
            return False

    try:
        if sys.platform == "win32":
            appdata = os.environ.get("APPDATA")
            if appdata:
                _prepend_path(Path(appdata) / "npm")
                _add_to_user_path_windows(Path(appdata) / "npm")
        _run(["npm", "install", "-g", "appium"], check=True)
        _run(["appium", "driver", "install", "uiautomator2"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install Appium: {e}")
        if e.stderr:
            print(e.stderr.strip())
        return False

    return _have_cmd("appium")


def check_requirements(
    *,
    attempt_fix: bool = False,
    install_node: bool = False,
    install_adb_cli: bool = False,
    install_appium_cli: bool = False,
    yes: bool = False,
) -> bool:
    """Check if required tools are installed; optionally attempt installation."""
    checks: dict[str, str] = {
        "Python": f"✅ {sys.executable}",
        "adb": "❌ Not found",
        "node": "❌ Not found",
        "npm": "❌ Not found",
        "appium": "❌ Not found",
    }

    # Check adb
    try:
        result = _run(["adb", "version"], check=False)
        if result.returncode == 0:
            checks["adb"] = "✅ Installed"
        else:
            checks["adb"] = "❌ Not found"
    except FileNotFoundError:
        checks["adb"] = "❌ Not found"

    # Check node/npm
    if _have_cmd("node"):
        try:
            node_v = _run(["node", "--version"], check=False).stdout.strip() or "installed"
            checks["node"] = f"✅ Installed ({node_v})"
        except Exception:
            checks["node"] = "✅ Installed"
    if _have_cmd("npm"):
        try:
            npm_v = _run(["npm", "--version"], check=False).stdout.strip() or "installed"
            checks["npm"] = f"✅ Installed ({npm_v})"
        except Exception:
            checks["npm"] = "✅ Installed"

    # Check appium
    try:
        result = _run(["appium", "--version"], check=False)
        if result.returncode == 0:
            checks["appium"] = f"✅ Installed ({result.stdout.strip()})"
        else:
            checks["appium"] = "❌ Not found"
    except FileNotFoundError:
        checks["appium"] = "❌ Not found"

    print("\n📋 Requirements Check:")
    print(f"  Python: {checks['Python']}")
    print(f"  adb: {checks['adb']}")
    print(f"  node: {checks['node']}")
    print(f"  npm: {checks['npm']}")
    print(f"  appium: {checks['appium']}")

    if "❌" in checks["adb"]:
        print("\n⚠️  adb is not installed. Please install Android SDK Platform-Tools.")
        print("   Visit: https://developer.android.com/studio/releases/platform-tools")

    if ("❌" in checks["node"] or "❌" in checks["npm"]) and not (attempt_fix and install_node):
        print("\n⚠️  Node.js/npm is not installed.")
        print("   Install Node.js: https://nodejs.org/")

    if "❌" in checks["appium"] and not (attempt_fix and install_appium_cli):
        print("\n⚠️  Appium is not installed.")
        print("   npm install -g appium")
        print("   appium driver install uiautomator2")

    if attempt_fix and install_node and ("❌" in checks["node"] or "❌" in checks["npm"]):
        print("\n🔧 Installing Node.js/npm...")
        if install_nodejs_npm(yes=yes):
            print("✅ Node.js/npm installed")
        else:
            print("❌ Node.js/npm installation failed or was skipped")

    if attempt_fix and install_adb_cli and "❌" in checks["adb"]:
        print("\n🔧 Installing adb (Android Platform-Tools)...")
        if install_adb(yes=yes):
            print("✅ adb installed")
        else:
            print("❌ adb installation failed or was skipped")

    if attempt_fix and install_appium_cli and "❌" in checks["appium"]:
        print("\n🔧 Installing Appium + uiautomator2 driver...")
        if install_appium(yes=yes):
            print("✅ Appium installed")
        else:
            print("❌ Appium installation failed or was skipped")

    # Re-check for final status
    ok_adb = _have_cmd("adb")
    ok_appium = _have_cmd("appium")
    return ok_adb and ok_appium


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
    parser.add_argument(
        "--no-register",
        action="store_true",
        help="Install/check requirements but skip Claude Code registration",
    )
    parser.add_argument(
        "--install-deps",
        action="store_true",
        help="Attempt to install adb + Node.js/npm + Appium (where supported)",
    )
    parser.add_argument(
        "--install-adb",
        action="store_true",
        help="Attempt to install adb (Windows only)",
    )
    parser.add_argument(
        "--install-node",
        action="store_true",
        help="Attempt to install Node.js/npm (macOS/Linux/Windows via winget/choco)",
    )
    parser.add_argument(
        "--install-appium",
        action="store_true",
        help="Attempt to install Appium + uiautomator2 via npm",
    )
    parser.add_argument(
        "-y",
        "--yes",
        action="store_true",
        help="Assume 'yes' for installation prompts",
    )

    args = parser.parse_args()

    print("=" * 60)
    print("MCP Appium Installer")
    print("=" * 60)

    if args.check:
        check_requirements()
        return

    if args.install_deps:
        args.install_node = True
        args.install_adb = True
        args.install_appium = True

    if args.uninstall:
        if unregister_from_claude_code():
            print("\n✅ Uninstallation complete!")
        else:
            print("\n❌ Uninstallation failed!")
            sys.exit(1)
        return

    # Installation
    print("\n1. Checking requirements...")
    all_ok = check_requirements(
        attempt_fix=True,
        install_node=args.install_node,
        install_adb_cli=args.install_adb,
        install_appium_cli=args.install_appium,
        yes=args.yes,
    )

    if not all_ok:
        print("\n⚠️  Some requirements are missing. Please install them first.")
        if args.install_node or args.install_appium:
            print("   (Automatic install may have been skipped or failed.)")
        if not args.yes:
            response = input("\nContinue anyway? (y/N): ")
            if response.lower() != "y":
                print("Installation cancelled.")
                sys.exit(1)

    if args.no_register:
        print("\n2. Skipping Claude Code registration (--no-register).")
        print("\n" + "=" * 60)
        print("✅ Requirements step complete!")
        print("=" * 60)
        return

    print("\n2. Registering MCP server with Claude Code...")
    if not register_with_claude_code():
        print("\n❌ Installation failed!")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("✅ Installation complete!")
    print("=" * 60)
    print("\n📝 Next steps:")
    print("  1. Restart Claude Code")
    print("  2. Connect an Android device or start an emulator")
    print("  3. In Claude Code, say: 'Setup Appium and connect to my device'")
    print("\n💡 Tip: Use 'list_devices' to see connected devices first")


if __name__ == "__main__":
    main()
