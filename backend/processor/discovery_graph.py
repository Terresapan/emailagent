#!/usr/bin/env python3
"""
Generate Mermaid diagram of the Viral App Discovery workflow.
Run from project root: python processor/discovery_graph.py
"""
import sys
import os

# Get the absolute path to the project root (two levels up from this script)
# Script is at: backend/processor/discovery_graph.py
# Root is: backend/
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)

# Add project root to path
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# CRITICAL: Remove the script's directory from sys.path if it was added by Python
# This prevents "import email" from importing backend/processor/email instead of stdlib
if script_dir in sys.path:
    sys.path.remove(script_dir)

# MOCK Dependencies to avoid installation
# The graph definition imports ArcadeClient which imports arcadepy.
# We mock it here to allow graph generation without installing the package.
import types
from unittest.mock import MagicMock

# Create a mock package for arcadepy
arcadepy = types.ModuleType("arcadepy")
arcadepy.__path__ = []  # Mark as a package
sys.modules["arcadepy"] = arcadepy

# Mock Arcade class
arcadepy.Arcade = MagicMock()

# Mock submodules
sys.modules["arcadepy.types"] = types.ModuleType("arcadepy.types")
sys.modules["arcadepy.types"].__path__ = []

# Mock execute_tool_response module
execute_tool_response = types.ModuleType("arcadepy.types.execute_tool_response")
sys.modules["arcadepy.types.execute_tool_response"] = execute_tool_response
# Mock OutputError
execute_tool_response.OutputError = Exception

# Mock YouTube Transcript API
youtube_transcript_api = types.ModuleType("youtube_transcript_api")
youtube_transcript_api.__path__ = []
sys.modules["youtube_transcript_api"] = youtube_transcript_api
sys.modules["youtube_transcript_api.YouTubeTranscriptApi"] = MagicMock()

# Mock youtube_transcript_api._errors
youtube_transcript_errors = types.ModuleType("youtube_transcript_api._errors")
sys.modules["youtube_transcript_api._errors"] = youtube_transcript_errors
youtube_transcript_errors.TranscriptsDisabled = Exception
youtube_transcript_errors.NoTranscriptFound = Exception

# Mock googleapiclient (used in Gmail/YouTube sources)
googleapiclient = types.ModuleType("googleapiclient")
googleapiclient.__path__ = []
sys.modules["googleapiclient"] = googleapiclient
sys.modules["googleapiclient.discovery"] = MagicMock()
sys.modules["googleapiclient.errors"] = MagicMock()
sys.modules["googleapiclient.errors"].HttpError = Exception

# Mock google.auth and google_auth_oauthlib
sys.modules["google"] = types.ModuleType("google")
sys.modules["google"].__path__ = []
sys.modules["google.auth"] = types.ModuleType("google.auth")
sys.modules["google.auth"].__path__ = []
sys.modules["google.auth.transport"] = types.ModuleType("google.auth.transport")
sys.modules["google.auth.transport"].__path__ = []
sys.modules["google.auth.transport.requests"] = MagicMock()

sys.modules["google_auth_oauthlib"] = types.ModuleType("google_auth_oauthlib")
sys.modules["google_auth_oauthlib"].__path__ = []
sys.modules["google_auth_oauthlib.flow"] = MagicMock()

from processor.viral_app.graph import DiscoveryGraph


def main():
    """Generate and save the graph diagram as PNG with all nodes expanded."""
    print("Initializing DiscoveryGraph to build graph...")
    # Initialize in test mode to minimize initialization overhead
    workflow = DiscoveryGraph(test_mode=True)
    
    # Use xray=True to expand subgraphs and show all internal nodes
    # Assuming workflow.graph is the compiled StateGraph
    if hasattr(workflow, 'graph'):
        graph = workflow.graph.get_graph(xray=True)
    elif hasattr(workflow, 'app'):
        # Some implementations call the compiled graph 'app'
        graph = workflow.app.get_graph(xray=True)
    else:
        print("Error: Could not find compiled graph attribute (graph or app) on DiscoveryGraph")
        return
    
    # Generate PNG
    png_file = os.path.join(script_dir, "discovery.png")
    print(f"Generating PNG diagram with all nodes expanded...")
    
    try:
        png_data = graph.draw_mermaid_png()
        with open(png_file, "wb") as f:
            f.write(png_data)
        print(f"✓ Saved PNG to: {png_file}")
    except Exception as e:
        print(f"PNG generation failed: {e}")
        print("Falling back to Mermaid text file...")
        
        # Fallback to mmd file
        mmd_file = os.path.join(script_dir, "discovery.mmd")
        mermaid_diagram = graph.draw_mermaid()
        with open(mmd_file, "w") as f:
            f.write(mermaid_diagram)
        print(f"Saved Mermaid to: {mmd_file}")
        print("Paste contents into https://mermaid.live to visualize")


if __name__ == "__main__":
    main()
