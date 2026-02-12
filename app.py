import streamlit as st
from core.ui import load_css
from core.auth import require_auth
from core.supa import supabase_user
from core.queries import get_profile

st.set_page_config(page_title="PulseAgenda", layout="wide")
uid = require_auth(); sb = supabase_user()
prof = get_profile(sb, uid) or {}
focus = (prof.get("theme") == "focus")
load_css(focus_mode=focus)

st.title("PulseAgenda")
st.caption("Seu ritmo. Seu foco. Sua agenda.")
