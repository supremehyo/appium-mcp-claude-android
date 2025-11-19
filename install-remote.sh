#!/bin/bash
# Remote installation script for mcp-appium
# Usage: curl -sSL https://raw.githubusercontent.com/supremehyo/appium-mcp-claude-android/main/install-remote.sh | bash

set -e

REPO_URL="https://github.com/supremehyo/appium-mcp-claude-android.git"
INSTALL_DIR="$HOME/.mcp-appium"

echo "=========================================="
echo "MCP Appium - Remote Installer"
echo "=========================================="
echo ""

# Check if git is installed
if ! command -v git &> /dev/null; then
    echo "❌ Git is not installed. Please install git first."
    exit 1
fi

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or later."
    exit 1
fi

echo "✅ Git found: $(git --version)"
echo "✅ Python found: $(python3 --version)"
echo ""

# Clone or update repository
if [ -d "$INSTALL_DIR" ]; then
    echo "📦 Updating existing installation..."
    cd "$INSTALL_DIR"
    git pull
else
    echo "📦 Cloning repository..."
    git clone "$REPO_URL" "$INSTALL_DIR"
    cd "$INSTALL_DIR"
fi

echo ""
echo "📦 Installing Python package..."
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

# Create .mcp.json in installation directory
echo ""
echo "📝 Creating .mcp.json for MCP server configuration..."
PYTHON_PATH=$(which python3)
cat > "$INSTALL_DIR/.mcp.json" <<EOF
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
echo "  1. Navigate to the installation directory: cd $INSTALL_DIR"
echo "  2. Open Claude Code in that directory"
echo "  3. Claude Code will automatically detect .mcp.json"
echo "  4. Approve the MCP server when prompted"
echo "  5. Connect an Android device or start an emulator"
echo "  6. Say: 'Setup Appium and connect to my device'"
echo ""
echo "💡 Tip: To use in other projects, copy .mcp.json from $INSTALL_DIR"
echo ""
echo "📚 Documentation: $INSTALL_DIR/README.md"
