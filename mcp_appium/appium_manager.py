"""Appium server management utilities."""

from __future__ import annotations

import logging
import subprocess
import time
import signal
import os
import requests
from typing import Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class AppiumServerManager:
    """Manages Appium server lifecycle."""

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 4723,
        log_file: Optional[str] = None,
    ):
        self.host = host
        self.port = port
        self.log_file = log_file
        self.process: Optional[subprocess.Popen] = None
        self.base_path = "/"

    @property
    def server_url(self) -> str:
        """Get the server URL."""
        return f"http://{self.host}:{self.port}"

    def is_running(self) -> bool:
        """Check if Appium server is running."""
        try:
            response = requests.get(
                f"{self.server_url}/status",
                timeout=2,
            )
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False

    def start(self, timeout: int = 30) -> bool:
        """
        Start Appium server.

        Args:
            timeout: Maximum time to wait for server to start (seconds)

        Returns:
            True if server started successfully, False otherwise
        """
        # Check if server is already running
        if self.is_running():
            logger.info(f"Appium server already running at {self.server_url}")
            return True

        logger.info(f"Starting Appium server at {self.server_url}...")

        # Prepare command
        cmd = [
            "appium",
            "--address", self.host,
            "--port", str(self.port),
            "--base-path", self.base_path,
            "--relaxed-security",
        ]

        # Setup log file
        log_handle = None
        if self.log_file:
            log_path = Path(self.log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            log_handle = open(log_path, "w")
            logger.info(f"Appium logs will be written to: {log_path}")

        try:
            # Start Appium server process
            self.process = subprocess.Popen(
                cmd,
                stdout=log_handle or subprocess.PIPE,
                stderr=subprocess.STDOUT,
                preexec_fn=os.setsid if os.name != 'nt' else None,
            )

            # Wait for server to be ready
            start_time = time.time()
            while time.time() - start_time < timeout:
                if self.is_running():
                    logger.info(f"Appium server started successfully at {self.server_url}")
                    return True
                time.sleep(0.5)

            # Timeout reached
            logger.error(f"Appium server failed to start within {timeout} seconds")
            self.stop()
            return False

        except FileNotFoundError:
            logger.error(
                "Appium not found. Please install it: npm install -g appium"
            )
            if log_handle:
                log_handle.close()
            return False
        except Exception as e:
            logger.error(f"Failed to start Appium server: {e}")
            if log_handle:
                log_handle.close()
            return False

    def stop(self) -> None:
        """Stop Appium server."""
        if self.process:
            logger.info("Stopping Appium server...")
            try:
                # Try graceful shutdown first
                if os.name != 'nt':
                    os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
                else:
                    self.process.terminate()

                # Wait for process to exit
                try:
                    self.process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    # Force kill if still running
                    if os.name != 'nt':
                        os.killpg(os.getpgid(self.process.pid), signal.SIGKILL)
                    else:
                        self.process.kill()
                    self.process.wait()

                logger.info("Appium server stopped")
            except Exception as e:
                logger.error(f"Error stopping Appium server: {e}")
            finally:
                self.process = None

    def restart(self, timeout: int = 30) -> bool:
        """
        Restart Appium server.

        Args:
            timeout: Maximum time to wait for server to start (seconds)

        Returns:
            True if server restarted successfully, False otherwise
        """
        self.stop()
        time.sleep(2)  # Wait a bit before restarting
        return self.start(timeout)

    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()
