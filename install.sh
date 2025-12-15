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

INSTALLER_ARGS=(--no-register --install-node --install-appium)
if [[ "${MCP_APPIUM_YES:-}" == "1" || "${MCP_APPIUM_YES:-}" == "y" || "${MCP_APPIUM_YES:-}" == "Y" ]]; then
    INSTALLER_ARGS+=(-y)
fi
python3 -m mcp_appium.installer "${INSTALLER_ARGS[@]}"

# Ensure .mcp.json exists (repo includes a default one).
echo ""
if [ -f ".mcp.json" ]; then
    echo "✅ .mcp.json already exists"
else
    echo "📝 Creating .mcp.json for this project..."
    cat > .mcp.json <<'EOF'
{
  "mcpServers": {
    "appium": {
      "type": "stdio",
      "command": "python3",
      "args": ["-m", "mcp_appium.server"]
    }
  }
}
EOF
    echo "✅ Created .mcp.json"
fi

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
