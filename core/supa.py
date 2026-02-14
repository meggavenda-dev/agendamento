# core/supa.py
import os
import json
import uuid
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
        raise RuntimeError(
            "Configure SUPABASE_URL e SUPABASE_ANON_KEY em .streamlit/secrets.toml"
        )
    return create_client(url, key)

# ---------------- Normalização de sessão ----------------
def _extract(obj, key, default=None):
    if obj is None:
        return default
    v = getattr(obj, key, None)
    if v is not None:
        return v
    if isinstance(obj, dict):
        return obj.get(key, default)
    return default

def _normalize_user(user_obj):
    if not user_obj:
        return None
    return {
        "id": _extract(user_obj, "id"),
        "email": (_extract(user_obj, "email") or "").strip().lower(),
    }

def normalize_session(sess_obj):
    """
    Converte o objeto de sessão do supabase-py em um dict JSON‑serializável.
    """
    if not sess_obj:
        return None
    return {
        "access_token": _extract(sess_obj, "access_token"),
        "refresh_token": _extract(sess_obj, "refresh_token"),
        "user": _normalize_user(_extract(sess_obj, "user")),
    }

# ---------------- Persistência local ----------------
def _device_id() -> str:
    if "device_id" not in st.session_state:
        st.session_state["device_id"] = str(uuid.uuid4())
    return st.session_state["device_id"]

def _session_path() -> str:
    return os.path.join(SESS_DIR, f"{_device_id()}.json")

def save_session_to_file(session_obj):
    """
    Salva apenas a versão normalizada (dict) para garantir JSON válido.
    """
    try:
        data = normalize_session(session_obj) if session_obj else None
        if not data:
            return
        with open(_session_path(), "w", encoding="utf-8") as f:
            json.dump(data, f)
    except Exception:
        # não interrompe o app caso falhe
        pass

def load_session_from_file():
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

# ---------------- Restauração de sessão ----------------
def supabase_user():
    """
    Retorna cliente Supabase com sessão restaurada (se houver) e
    garante que st.session_state['sb_user'] seja preenchido.
    """
    sb = supabase_anon()

    # 1) memória
    sess = st.session_state.get("sb_session")

    # 2) arquivo, se necessário
    if not sess:
        saved = load_session_from_file()
        if saved:
            sess = saved
            st.session_state["sb_session"] = saved  # já é dict normalizado

    if not sess:
        return sb  # anônimo

    access_token = _extract(sess, "access_token")
    refresh_token = _extract(sess, "refresh_token")

    if not refresh_token:
        # sem refresh_token não dá para manter
        return sb

    try:
        if access_token:
            sb.auth.set_session(access_token, refresh_token)
        else:
            sb.auth.refresh_session()

        current = sb.auth.get_session()
        if current and current.session:
            norm = normalize_session(current.session)
            st.session_state["sb_session"] = norm
            save_session_to_file(norm)

        # Garante sb_user preenchido (para current_user_* funcionar)
        try:
            u = sb.auth.get_user()
            user_obj = getattr(u, "user", None) if u else None
            if user_obj:
                st.session_state["sb_user"] = _normalize_user(user_obj)
        except Exception:
            pass

        return sb
    except Exception:
        # última tentativa: refresh explícito
        try:
            sb.auth.refresh_session()
            current = sb.auth.get_session()
            if current and current.session:
                norm = normalize_session(current.session)
                st.session_state["sb_session"] = norm
                save_session_to_file(norm)
                try:
                    u = sb.auth.get_user()
                    user_obj = getattr(u, "user", None) if u else None
                    if user_obj:
                        st.session_state["sb_user"] = _normalize_user(user_obj)
                except Exception:
                    pass
                return sb
        except Exception:
            pass

    # falhou: limpa e segue anônimo
    for k in ("sb_session", "sb_user", "login_email"):
        st.session_state.pop(k, None)
    clear_saved_session()
    return sb
