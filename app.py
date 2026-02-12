
import streamlit as st
from core.ui import load_css
from core.auth import require_auth

st.set_page_config(page_title="PulseAgenda", layout="wide")
load_css()
_ = require_auth()

st.title("PulseAgenda")
st.write("Use o menu lateral: Agora | Semana | Criar | Foco do Dia | Pomodoro | Entrada Rapida | Config | Exportar")
