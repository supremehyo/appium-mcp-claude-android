#!/bin/bash
# Quick installation script for mcp-appium

set -e

echo "=========================================="
echo "MCP Appium - Quick Installer"
echo "=========================================="
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or later."
    exit 1
fi

echo "✅ Python found: $(python3 --version)"

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 is not installed. Please install pip."
    exit 1
fi

echo "✅ pip found"

# Install the package
echo ""
echo "📦 Installing mcp-appium package..."
pip3 install -e .

# Check requirements
echo ""
echo "🔍 Checking requirements..."

if ! command -v adb &> /dev/null; then
    echo "⚠️  adb not found. Please install Android SDK Platform-Tools."
    echo "   Visit: https://developer.android.com/studio/releases/platform-tools"
else
    echo "✅ adb found"
fi

if ! command -v appium &> /dev/null; then
    echo "⚠️  Appium not found. Installing now..."
    if command -v npm &> /dev/null; then
        npm install -g appium
        appium driver install uiautomator2
        echo "✅ Appium installed"
    else
        echo "❌ npm not found. Please install Node.js and npm first."
        echo "   Visit: https://nodejs.org/"
        exit 1
    fi
else
    echo "✅ Appium found: $(appium --version)"
fi

# Register with Claude Code
echo ""
echo "📝 Registering MCP server with Claude Code..."
python3 -m mcp_appium.installer

echo ""
echo "=========================================="
echo "Installation Complete! 🎉"
echo "=========================================="
echo ""
echo "📝 Next steps:"
echo "  1. Restart Claude Code"
echo "  2. Connect an Android device or start an emulator"
echo "  3. In Claude Code, say: 'Setup Appium and connect to my device'"
echo ""
echo "💡 Tip: Use '/mcp list' to verify the server is registered"
