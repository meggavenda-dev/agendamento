import os
import streamlit as st
from supabase import create_client


def _get(name: str, default: str = "") -> str:
    """Lê configuração por st.secrets (Streamlit Cloud) ou os.environ (local)."""
    if name in st.secrets:
        return str(st.secrets.get(name))
    return os.environ.get(name, default)


def allowed_email() -> str:
    """
    E-mail permitido para login.
    Você pode definir em Secrets como SUPABASE_ALLOWED_EMAIL,
    ou deixar fixo aqui.
    """
    return _get("SUPABASE_ALLOWED_EMAIL", "guilherme.h.cavalcante@gmail.com").strip().lower()


@st.cache_resource(show_spinner=False)
def supabase_anon():
    """
    Client Supabase usando ANON KEY.
    Serve para Auth (login) e leituras públicas (se existirem).
    """
    url = _get("SUPABASE_URL")
    key = _get("SUPABASE_ANON_KEY")
    if not url or not key:
        raise RuntimeError("Configure SUPABASE_URL e SUPABASE_ANON_KEY em Secrets/ENV.")
    return create_client(url, key)


def supabase_user():
    """
    Client Supabase com a sessão do usuário aplicada.
    Isso é ESSENCIAL para passar pelas policies de RLS em inserts/updates.
    Usa auth.set_session(access_token, refresh_token). [1](https://github.com/orgs/supabase/discussions/22578)
    """
    sb = supabase_anon()

    sess = st.session_state.get("sb_session")
    if sess:
        # sess pode ser objeto (sess.access_token) ou dict
        access_token = getattr(sess, "access_token", None) or (sess.get("access_token") if isinstance(sess, dict) else None)
        refresh_token = getattr(sess, "refresh_token", None) or (sess.get("refresh_token") if isinstance(sess, dict) else None)

        if access_token and refresh_token:
            sb.auth.set_session(access_token, refresh_token)  # [1](https://github.com/orgs/supabase/discussions/22578)

    return sb
