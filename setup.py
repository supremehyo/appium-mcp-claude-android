"""Setup script for mcp-appium package."""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

setup(
    name="mcp-appium",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="MCP Server for Appium mobile automation with auto-detection and setup",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/mcp-appium",
    packages=find_packages(exclude=["tests", "tests.*"]),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Testing",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.8",
    install_requires=[
        "appium-python-client>=3.2.1",
        "anthropic>=0.31.0",
        "mcp>=1.0.0",
        "requests>=2.31.0",
    ],
    entry_points={
        "console_scripts": [
            "mcp-appium=mcp_appium.server:main",
            "mcp-appium-install=mcp_appium.installer:main",
        ],
    },
    include_package_data=True,
    package_data={
        "mcp_appium": ["config/*.json"],
    },
)
