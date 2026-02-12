
import os
import streamlit as st
from supabase import create_client

def _get(name: str, default: str = "") -> str:
    if name in st.secrets:
        return str(st.secrets.get(name))
    return os.environ.get(name, default)

def allowed_email() -> str:
    return _get("SUPABASE_ALLOWED_EMAIL", "").strip().lower()

@st.cache_resource(show_spinner=False)
def supabase_anon():
    url = _get("SUPABASE_URL"); key = _get("SUPABASE_ANON_KEY")
    if not url or not key:
        raise RuntimeError("Configure SUPABASE_URL e SUPABASE_ANON_KEY")
    return create_client(url, key)

def supabase_user():
    sb = supabase_anon()
    sess = st.session_state.get("sb_session")
    if sess:
        access_token = getattr(sess, "access_token", None) or (sess.get("access_token") if isinstance(sess, dict) else None)
        refresh_token = getattr(sess, "refresh_token", None) or (sess.get("refresh_token") if isinstance(sess, dict) else None)
        if access_token and refresh_token:
            sb.auth.set_session(access_token, refresh_token)
    return sb
