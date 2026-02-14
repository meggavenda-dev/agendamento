# pages/0_Debug.py
import streamlit as st
from core.supa import allowed_email, supabase_user, load_session_from_file

st.title("DEBUG")
sb = supabase_user()

st.subheader("Secrets & Allowed")
st.write({
    "has_SUPABASE_URL": "SUPABASE_URL" in st.secrets,
    "has_SUPABASE_ANON_KEY": "SUPABASE_ANON_KEY" in st.secrets,
    "SUPABASE_ALLOWED_EMAIL": allowed_email(),
})

st.subheader("session_state keys")
st.write(list(st.session_state.keys()))

st.subheader("sb_session (state)")
st.write(st.session_state.get("sb_session"))

st.subheader("sb_user (state)")
st.write(st.session_state.get("sb_user"))

st.subheader("Saved file")
try:
    from core.supa import load_session_from_file  # import local
    st.write(load_session_from_file())
except Exception as e:
    st.write("load_session_from_file() error:", e)

st.caption("Remova esta página após o diagnóstico.")
