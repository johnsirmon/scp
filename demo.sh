#!/bin/bash
# SCP Demo Script - Shows the power of minimal case triage

echo "🚀 Support Context Protocol (SCP) Demo"
echo "=========================================="
echo ""

echo "📊 Current database stats:"
node scp.js stats
echo ""

echo "🔍 Search for all AMA-related cases:"
node scp.js search "AMA" 
echo ""

echo "🔍 Search for InfluxDB errors specifically:"
node scp.js search "InfluxDb"
echo ""

echo "📋 Get context for GitHub Copilot (JSON format):"
echo "node scp.js search \"AMA\" --context"
echo ""
echo "💡 This JSON can be copied and pasted into GitHub Copilot like:"
echo "'Help me debug this AMA issue: [PASTE_JSON_HERE]'"
echo ""

echo "🎯 Key Features Demonstrated:"
echo "✅ Smart ICM parsing (auto-extracted case IDs)"
echo "✅ PII redaction (subscription IDs → [SUB_ID_1])"
echo "✅ Log compression (repetitive entries compressed)"  
echo "✅ Cross-case search (find patterns across all cases)"
echo "✅ MCP-ready context export (perfect for AI tools)"
echo "✅ Zero setup (just Node.js + 2 npm packages)"
echo ""

echo "🔒 Privacy: All data stored locally in ~/.scp/"
echo "🚀 Perfect for Microsoft support engineers!"
