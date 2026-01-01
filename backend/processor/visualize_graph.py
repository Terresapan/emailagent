#!/usr/bin/env python3
"""
Generate Mermaid diagram of the LangGraph workflow.
Run from project root: python processor/visualize_graph.py
"""
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from processor.email.graph import EmailSummarizer


def main():
    """Generate and save the graph diagram as PNG with all nodes expanded."""
    print("Initializing EmailSummarizer to build graph...")
    summarizer = EmailSummarizer()
    
    # Use xray=True to expand subgraphs and show all internal nodes
    graph = summarizer.graph.get_graph(xray=True)
    
    # Generate PNG
    script_dir = os.path.dirname(os.path.abspath(__file__))
    png_file = os.path.join(script_dir, "graph.png")
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
        mmd_file = os.path.join(script_dir, "graph.mmd")
        mermaid_diagram = graph.draw_mermaid()
        with open(mmd_file, "w") as f:
            f.write(mermaid_diagram)
        print(f"Saved Mermaid to: {mmd_file}")
        print("Paste contents into https://mermaid.live to visualize")


if __name__ == "__main__":
    main()
