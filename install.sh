#!/bin/bash
# Installation script for mcp-appium

set -e

echo "=========================================="
echo "MCP Appium - Installer"
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
    echo "⚠️  Appium not found."
    if command -v npm &> /dev/null; then
        echo "   Installing Appium..."
        npm install -g appium
        appium driver install uiautomator2
        echo "✅ Appium installed"
    else
        echo "   Please install Node.js and npm first, then run:"
        echo "   npm install -g appium"
        echo "   appium driver install uiautomator2"
    fi
else
    echo "✅ Appium found: $(appium --version)"
fi

# Create .mcp.json in current directory
echo ""
echo "📝 Creating .mcp.json for this project..."
PYTHON_PATH=$(which python3)
cat > .mcp.json <<EOF
{
  "mcpServers": {
    "appium": {
      "type": "stdio",
      "command": "$PYTHON_PATH",
      "args": ["-m", "mcp_appium.server"]
    }
  }
}
EOF

echo "✅ Created .mcp.json"

echo ""
echo "=========================================="
echo "Installation Complete! 🎉"
echo "=========================================="
echo ""
echo "📝 Next steps:"
echo "  1. Open Claude Code in THIS directory"
echo "  2. Claude Code will automatically detect .mcp.json"
echo "  3. Approve the MCP server when prompted"
echo "  4. Connect an Android device or start an emulator"
echo "  5. In Claude Code, say: 'Setup Appium and connect to my device'"
echo ""
echo "💡 Tip: The MCP server is configured for THIS project only"
echo "   If you want to use it in other projects, copy .mcp.json there"
