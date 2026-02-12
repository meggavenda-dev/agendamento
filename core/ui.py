
import streamlit as st

def load_css(path: str = "assets/zen.css"):
    try:
        with open(path, "r", encoding="utf-8") as f:
            st.markdown("<style>"+f.read()+"</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        pass
