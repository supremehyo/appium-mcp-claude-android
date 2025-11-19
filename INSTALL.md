# Installation Guide

## Quick Install (Recommended)

### For End Users

1. **Clone or download the repository**
   ```bash
   git clone https://github.com/yourusername/mcp-appium.git
   cd mcp-appium
   ```

2. **Run the installation script**

   **macOS/Linux:**
   ```bash
   chmod +x install.sh
   ./install.sh
   ```

   **Windows:**
   ```bash
   pip install -e .
   python -m mcp_appium.installer
   ```

3. **Restart Claude Code**

4. **Verify installation**
   ```bash
   claude mcp list
   ```

   You should see `appium` in the list of MCP servers.

## Manual Installation

### 1. Install Prerequisites

**Node.js and Appium:**
```bash
# Install Node.js from https://nodejs.org/

# Install Appium globally
npm install -g appium

# Install UiAutomator2 driver
appium driver install uiautomator2
```

**Android SDK Platform-Tools (for adb):**
- Download from: https://developer.android.com/studio/releases/platform-tools
- Add to PATH

### 2. Install Python Package

**From source:**
```bash
cd mcp-appium
pip install -e .
```

**From PyPI (when published):**
```bash
pip install mcp-appium
```

### 3. Register with Claude Code

**Automatic:**
```bash
mcp-appium-install
```

**Manual:**
```bash
claude mcp add --transport stdio appium -- python -m mcp_appium.server
```

### 4. Verify Installation

```bash
# List MCP servers
claude mcp list

# Check requirements
mcp-appium-install --check
```

## Distribution for Others

### Option 1: Share Installation Script

Share the entire repository with users and have them run:
```bash
git clone <your-repo-url>
cd mcp-appium
./install.sh  # macOS/Linux
```

### Option 2: Publish to PyPI

1. **Build the package:**
   ```bash
   pip install build twine
   python -m build
   ```

2. **Upload to PyPI:**
   ```bash
   twine upload dist/*
   ```

3. **Users can install with:**
   ```bash
   pip install mcp-appium
   mcp-appium-install
   ```

### Option 3: Share as Wheel File

1. **Build the wheel:**
   ```bash
   python -m build
   ```

2. **Share the `.whl` file from `dist/` folder**

3. **Users install with:**
   ```bash
   pip install mcp_appium-0.1.0-py3-none-any.whl
   mcp-appium-install
   ```

## Uninstallation

```bash
# Unregister from Claude Code
mcp-appium-install --uninstall

# Uninstall the package
pip uninstall mcp-appium
```

## Troubleshooting

### "claude: command not found"
- Ensure Claude Code CLI is installed and in your PATH
- Try restarting your terminal

### "adb: command not found"
- Install Android SDK Platform-Tools
- Add to PATH: `export PATH=$PATH:/path/to/platform-tools`

### "appium: command not found"
- Install Node.js: https://nodejs.org/
- Install Appium: `npm install -g appium`

### MCP server not showing in Claude Code
- Run `claude mcp list` to check registration
- Restart Claude Code
- Try manual registration:
  ```bash
  claude mcp add --transport stdio appium -- python -m mcp_appium.server
  ```

## Development Setup

For developers who want to contribute:

```bash
# Clone the repository
git clone <your-repo-url>
cd mcp-appium

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in editable mode with dev dependencies
pip install -e ".[dev]"

# Register with Claude Code
python -m mcp_appium.installer
```
