"""Device detection and management utilities."""

from __future__ import annotations

import logging
import subprocess
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class DeviceInfo:
    """Information about a connected device."""

    def __init__(self, udid: str, status: str, model: str = "Unknown"):
        self.udid = udid
        self.status = status
        self.model = model

    def to_dict(self) -> Dict[str, str]:
        return {
            "udid": self.udid,
            "status": self.status,
            "model": self.model,
        }

    def __repr__(self) -> str:
        return f"DeviceInfo(udid={self.udid}, status={self.status}, model={self.model})"


def detect_android_devices(adb_binary: str = "adb") -> List[DeviceInfo]:
    """
    Detect connected Android devices using adb.

    Args:
        adb_binary: Path to adb binary (default: "adb")

    Returns:
        List of DeviceInfo objects for connected devices
    """
    try:
        result = subprocess.run(
            [adb_binary, "devices", "-l"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True,
            timeout=10,
        )
    except FileNotFoundError:
        logger.error(f"ADB binary not found: {adb_binary}")
        return []
    except subprocess.TimeoutExpired:
        logger.error("ADB devices command timed out")
        return []
    except subprocess.CalledProcessError as e:
        logger.error(f"ADB devices command failed: {e.stderr}")
        return []

    devices: List[DeviceInfo] = []
    lines = result.stdout.strip().split("\n")

    # Skip the first line ("List of devices attached")
    for line in lines[1:]:
        line = line.strip()
        if not line:
            continue

        # Parse line format: "udid status [model:... device:... ...]"
        parts = line.split(None, 1)
        if len(parts) < 2:
            continue

        udid = parts[0]
        rest = parts[1]

        # Extract status
        status_parts = rest.split(None, 1)
        status = status_parts[0]

        # Extract model if available
        model = "Unknown"
        if len(status_parts) > 1:
            metadata = status_parts[1]
            for item in metadata.split():
                if item.startswith("model:"):
                    model = item.split(":", 1)[1]
                    break

        devices.append(DeviceInfo(udid=udid, status=status, model=model))

    return devices


def get_first_available_device(adb_binary: str = "adb") -> DeviceInfo | None:
    """
    Get the first available (online) Android device.

    Args:
        adb_binary: Path to adb binary (default: "adb")

    Returns:
        DeviceInfo object or None if no device found
    """
    devices = detect_android_devices(adb_binary)

    # Filter for devices with "device" status (online and ready)
    online_devices = [d for d in devices if d.status == "device"]

    if not online_devices:
        logger.warning("No online Android devices found")
        return None

    if len(online_devices) > 1:
        logger.info(f"Multiple devices found, using first one: {online_devices[0].udid}")

    return online_devices[0]


def get_device_info(udid: str, adb_binary: str = "adb") -> Dict[str, Any]:
    """
    Get detailed information about a specific device.

    Args:
        udid: Device UDID
        adb_binary: Path to adb binary

    Returns:
        Dictionary with device information
    """
    info = {
        "udid": udid,
        "manufacturer": "Unknown",
        "model": "Unknown",
        "android_version": "Unknown",
    }

    try:
        # Get manufacturer
        result = subprocess.run(
            [adb_binary, "-s", udid, "shell", "getprop", "ro.product.manufacturer"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            info["manufacturer"] = result.stdout.strip()

        # Get model
        result = subprocess.run(
            [adb_binary, "-s", udid, "shell", "getprop", "ro.product.model"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            info["model"] = result.stdout.strip()

        # Get Android version
        result = subprocess.run(
            [adb_binary, "-s", udid, "shell", "getprop", "ro.build.version.release"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            info["android_version"] = result.stdout.strip()

    except Exception as e:
        logger.warning(f"Failed to get device info: {e}")

    return info
