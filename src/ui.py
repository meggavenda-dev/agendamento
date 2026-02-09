import streamlit as st

def badge(label: str, color: str):
    st.markdown(
        f"<span style='background:{color};color:white;padding:2px 8px;border-radius:999px;font-size:0.85em'>{label}</span>",
        unsafe_allow_html=True
    )
