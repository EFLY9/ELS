"""
Streamlit wrapper for the ELS Registration Assistant.
Runs the FastAPI app in a background thread and embeds it via iframe.
This preserves the custom HTML/CSS/JS UI while enabling Streamlit Cloud deployment.
"""
import os
import time
import threading
import socket
import streamlit as st

st.set_page_config(
    page_title="ELS Registration Assistant",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """<style>
    .stMainBlockContainer { padding: 0 !important; }
    iframe { border: none !important; }
    header[data-testid="stHeader"] { display: none !important; }
    .stAppDeployButton { display: none !important; }
    </style>""",
    unsafe_allow_html=True,
)


def find_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return s.getsockname()[1]


def start_fastapi(port):
    import uvicorn
    from app import app
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning")


if "fastapi_port" not in st.session_state:
    port = find_free_port()
    st.session_state.fastapi_port = port
    t = threading.Thread(target=start_fastapi, args=(port,), daemon=True)
    t.start()
    time.sleep(2)

port = st.session_state.fastapi_port
st.components.v1.iframe(f"http://127.0.0.1:{port}/", height=900, scrolling=True)
