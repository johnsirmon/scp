"""
Main module for running SCP components.
Provides entry points for CLI and API interfaces.
"""

import sys
from pathlib import Path

# Add the parent directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


def run_cli():
    """Run the SCP CLI interface."""
    from scp.cli import cli
    cli()


def run_api():
    """Run the SCP API server."""
    import uvicorn
    from scp.api import app
    
    print("🚀 Starting SCP API server...")
    print("📖 Interactive docs available at: http://localhost:8000/docs")
    print("🔍 Alternative docs at: http://localhost:8000/redoc")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "api":
        run_api()
    else:
        run_cli()
