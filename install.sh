#!/bin/bash
# SCP Installation Script

echo "Installing Support Context Protocol (SCP)..."

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "Node.js is required but not installed."
    echo "Please install Node.js from https://nodejs.org/"
    exit 1
fi

echo "Node.js found: $(node --version)"

# Install dependencies
echo "Installing dependencies..."
npm install

# Make scripts executable
chmod +x scp.js
chmod +x mcp-server.js

echo ""
echo "SCP Installation Complete!"
echo ""
echo "Quick Start:"
echo "  ./scp.js add --file your-icm.txt   # Add a case"
echo "  ./scp.js search 'error term'       # Search cases"
echo "  ./scp.js get CASE-123 --context    # Get AI context"
echo ""
echo "VSCode MCP Integration:"
echo "  Add to settings.json:"
echo "  {"
echo "    \"mcp.servers\": {"
echo "      \"scp\": {"
echo "        \"command\": \"node\","
echo "        \"args\": [\"$(pwd)/mcp-server.js\"]"
echo "      }"
echo "    }"
echo "  }"
echo ""
echo "See README.md for full documentation"
