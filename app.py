"""
Stock Analytics Agent - Main Streamlit Application

This is the main entry point for the Streamlit UI with:

- Interactive tabs: Live Conversation, Overview, Metrics, Valuation, Risk, Reports
- Provenance tracking for all calculations
- PDF report download

Run: streamlit run app.py
"""

import streamlit as st
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.streamlit_ui.main_ui import main as run_ui

# Configure page
st.set_page_config(
    page_title="Voice Stock Analytics Agent",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

if __name__ == "__main__":
    run_ui()
