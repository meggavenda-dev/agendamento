# app.py
import os
import sys
import streamlit as st

APP_ROOT = os.path.abspath(os.path.dirname(__file__))
if APP_ROOT not in sys.path:
    sys.path.insert(0, APP_ROOT)

from core.auth import require_auth
from core.supa import supabase_user
from core.ui import load_css
from core.queries import get_profile

st.set_page_config(page_title="PulseAgenda", layout="wide")

# 1) Restaura cliente/sessão (se existir)
sb = supabase_user()

# 2) Exige autenticação
uid = require_auth()

# 3) Reconfirma restauração para garantir tokens aplicados ao cliente AFTER auth
sb = supabase_user()

# 4) Perfil/tema
prof = get_profile(sb, uid) or {}
focus = (prof.get("theme") == "focus")
load_css(focus_mode=focus)

# 5) Conteúdo
st.title("PulseAgenda")
st.caption("Seu ritmo. Seu foco. Sua agenda.")
st.info("Use o menu lateral: Agora | Semana | Criar | Foco do Dia | Pomodoro | Entrada Rápida | Config | Exportar")
