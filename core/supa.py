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
    url = _get("SUPABASE_URL")
    key = _get("SUPABASE_ANON_KEY")
    if not url or not key:
        raise RuntimeError("Configure SUPABASE_URL e SUPABASE_ANON_KEY em .streamlit/secrets.toml")
    return create_client(url, key)

def _extract_token(sess, key):
    # Suporta objetos da SDK e dicts
    if not sess:
        return None
    val = getattr(sess, key, None)
    if val:
        return val
    if isinstance(sess, dict):
        return sess.get(key)
    return None

def supabase_user():
    """
    Retorna o cliente Supabase com sessão do usuário, se disponível.
    - Não quebra se não houver tokens.
    - Tenta refresh dos tokens expirada/os.
    - Limpa st.session_state ao falhar, forçando novo login limpo.
    """
    sb = supabase_anon()
    sess = st.session_state.get("sb_session")

    # Se não temos sessão em memória, retorna cliente anônimo (require_auth lidará com isso)
    if not sess:
        return sb

    access_token  = _extract_token(sess, "access_token")
    refresh_token = _extract_token(sess, "refresh_token")

    # Se não temos tokens válidos, retorna anônimo (require_auth bloqueia a página)
    if not access_token or not refresh_token:
        return sb

    try:
        # 1) Tenta aplicar sessão (se válida, segue)
        sb.auth.set_session(access_token, refresh_token)

        # 2) (opcional) Obtém sessão atual já normalizada pela SDK
        current = sb.auth.get_session()
        if current and current.session:
            # Atualiza sessão em memória (mantém tokens atualizados)
            st.session_state["sb_session"] = current.session
        return sb

    except Exception:
        # Tenta um refresh explícito; se falhar, limpa e exige novo login
        try:
            sb.auth.refresh_session()
            current = sb.auth.get_session()
            if current and current.session:
                st.session_state["sb_session"] = current.session
                return sb
        except Exception:
            pass

        # Limpa sessão inválida e força novo login numa próxima chamada de require_auth
        for k in ("sb_session", "sb_user", "login_email"):
            st.session_state.pop(k, None)

        return sb  # anônimo; a página com require_auth() vai bloquear e exibir login
