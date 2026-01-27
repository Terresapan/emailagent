#!/usr/bin/env python3
"""
Generate Mermaid diagram of the LangGraph workflow.
Run from project root: python processor/visualize_graph.py
"""
import sys
import os

# Get the absolute path to the project root (two levels up from this script)
# Script is at: backend/processor/visualize_graph.py
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

# Now we can safely import using the package path relative to backend/
from processor.email.graph import EmailSummarizer


def main():
    """Generate and save the graph diagram as PNG with all nodes expanded."""
    print("Initializing EmailSummarizer to build graph...")
    summarizer = EmailSummarizer()
    
    # Use xray=True to expand subgraphs and show all internal nodes
    graph = summarizer.graph.get_graph(xray=True)
    
    # Generate PNG
    script_dir = os.path.dirname(os.path.abspath(__file__))
    png_file = os.path.join(script_dir, "briefing.png")
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
        mmd_file = os.path.join(script_dir, "briefing.mmd")
        mermaid_diagram = graph.draw_mermaid()
        with open(mmd_file, "w") as f:
            f.write(mermaid_diagram)
        print(f"Saved Mermaid to: {mmd_file}")
        print("Paste contents into https://mermaid.live to visualize")


if __name__ == "__main__":
    main()
