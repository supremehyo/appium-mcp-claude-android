#!/bin/bash
# Remote installation script for mcp-appium
# Usage: curl -sSL https://raw.githubusercontent.com/supremehyo/appium-mcp-claude-android/main/install-remote.sh | bash

set -e

REPO_URL="https://github.com/supremehyo/appium-mcp-claude-android.git"
INSTALL_DIR="$HOME/.mcp-appium"
AUTO_YES="${MCP_APPIUM_YES:-}"

confirm() {
    local prompt="$1"
    if [[ "$AUTO_YES" == "1" || "$AUTO_YES" == "y" || "$AUTO_YES" == "Y" ]]; then
        return 0
    fi
    read -r -p "$prompt (y/N): " response
    [[ "$response" == "y" || "$response" == "Y" ]]
}

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
    if [ -n "$(git status --porcelain 2>/dev/null)" ]; then
        echo "⚠️  Existing installation has local changes."
        echo "   To discard them and continue, re-run with: MCP_APPIUM_CLEAN=1"
        if [[ "${MCP_APPIUM_CLEAN:-}" == "1" ]] || confirm "Discard local changes (git reset --hard && git clean -fd)?"; then
            git reset --hard
            git clean -fd
        else
            exit 1
        fi
    fi
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

INSTALLER_ARGS=(--no-register --install-node --install-appium)
if [[ "${AUTO_YES:-}" == "1" || "${AUTO_YES:-}" == "y" || "${AUTO_YES:-}" == "Y" ]]; then
    INSTALLER_ARGS+=(-y)
fi
python3 -m mcp_appium.installer "${INSTALLER_ARGS[@]}"

# Ensure .mcp.json exists (repo includes a default one).
echo ""
if [ -f "$INSTALL_DIR/.mcp.json" ]; then
    echo "✅ .mcp.json already exists"
else
    echo "📝 Creating .mcp.json for MCP server configuration..."
    cat > "$INSTALL_DIR/.mcp.json" <<'EOF'
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
