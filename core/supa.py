# core/supa.py
import os, json, uuid
import streamlit as st
from supabase import create_client

SESS_DIR = os.path.join(".streamlit", "sessions")
os.makedirs(SESS_DIR, exist_ok=True)

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

# ---------------- Persistência local ----------------
def _device_id() -> str:
    if "device_id" not in st.session_state:
        st.session_state["device_id"] = str(uuid.uuid4())
    return st.session_state["device_id"]

def _session_path() -> str:
    return os.path.join(SESS_DIR, f"{_device_id()}.json")

def save_session_to_file(session_obj: dict | None):
    try:
        if not session_obj:
            return
        with open(_session_path(), "w", encoding="utf-8") as f:
            json.dump(session_obj, f)
    except Exception:
        pass

def load_session_from_file() -> dict | None:
    try:
        p = _session_path()
        if not os.path.exists(p):
            return None
        with open(p, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None

def clear_saved_session():
    try:
        p = _session_path()
        if os.path.exists(p):
            os.remove(p)
    except Exception:
        pass

# ---------------- Restauração segura ----------------
def _extract(obj, key):
    if not obj:
        return None
    v = getattr(obj, key, None)
    if v:
        return v
    if isinstance(obj, dict):
        return obj.get(key)
    return None

def supabase_user():
    """
    Retorna um cliente Supabase *com sessão restaurada*, se houver.

    Ordem:
    1) Usa st.session_state["sb_session"], se existir;
    2) Se não, tenta arquivo salvo (persistência por dispositivo);
    3) Se tokens expirados, tenta refresh;
    4) Caso falhe, limpa e retorna cliente anônimo.
    """
    sb = supabase_anon()

    # Fonte 1: sessão viva em memória
    sess = st.session_state.get("sb_session")

    # Fonte 2: arquivo salvo (se não tiver em memória)
    if not sess:
        sess = load_session_from_file()
        if sess:
            st.session_state["sb_session"] = sess  # sincroniza memória

    if not sess:
        return sb  # anônimo; require_auth bloqueará em seguida

    access_token = _extract(sess, "access_token")
    refresh_token = _extract(sess, "refresh_token")
    if not refresh_token:
        return sb

    try:
        # aplica a sessão; supabase-py pode auto-refresh depois
        if access_token:
            sb.auth.set_session(access_token, refresh_token)
        else:
            sb.auth.refresh_session()

        current = sb.auth.get_session()
        if current and current.session:
            st.session_state["sb_session"] = current.session
            save_session_to_file(current.session)
        return sb
    except Exception:
        # última tentativa: refresh explícito
        try:
            sb.auth.refresh_session()
            current = sb.auth.get_session()
            if current and current.session:
                st.session_state["sb_session"] = current.session
                save_session_to_file(current.session)
                return sb
        except Exception:
            pass

    # falhou: limpa tudo
    for k in ("sb_session", "sb_user", "login_email"):
        st.session_state.pop(k, None)
    clear_saved_session()
    return sb
