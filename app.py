import streamlit as st
from core.ui import load_css
from core.auth import require_auth

st.set_page_config(page_title="PulseAgenda", layout="wide")
load_css()

_ = require_auth()

st.title("PulseAgenda")
st.caption("Seu ritmo. Seu foco. Sua agenda.")
st.divider()

st.info("Use o menu lateral para navegar: ⚡ Agora | 🗓️ Semana | ➕ Criar | ⚙️ Config")
