
import streamlit as st
from core.supa import supabase_anon, supabase_user, allowed_email

def _n(email: str) -> str:
    return (email or "").strip().lower()

def current_user():
    user = st.session_state.get("sb_user")
    if user: return user
    sess = st.session_state.get("sb_session")
    if not sess: return None
    return getattr(sess, "user", None) or (sess.get("user") if isinstance(sess, dict) else None)

def current_user_email() -> str:
    u = current_user(); e = getattr(u, "email", None) if u else None
    if not e and isinstance(u, dict): e = u.get("email")
    return _n(e)

def current_user_id():
    u = current_user(); uid = getattr(u, "id", None) if u else None
    if not uid and isinstance(u, dict): uid = u.get("id")
    return uid

def logout():
    try:
        supabase_anon().auth.sign_out()
    except Exception:
        pass
    for k in ["sb_session","sb_user","login_email"]:
        st.session_state.pop(k, None)
    st.rerun()

def login_box():
    st.subheader("Entrar no PulseAgenda")
    allowed = allowed_email() or ""
    st.caption("Acesso restrito ao e-mail permitido nas configurações.")
    email = st.text_input("E-mail", value=allowed, disabled=bool(allowed))
    password = st.text_input("Senha", type="password")
    if st.button("Entrar", use_container_width=True):
        if allowed and _n(email) != _n(allowed):
            st.error("E-mail não permitido."); st.stop()
        sb = supabase_anon()
        try:
            res = sb.auth.sign_in_with_password({"email": _n(email), "password": password})
            session = getattr(res, "session", None) or (res.get("session") if isinstance(res, dict) else None)
            user = getattr(res, "user", None) or (res.get("user") if isinstance(res, dict) else None)
            st.session_state["sb_session"] = session
            st.session_state["sb_user"] = user
            st.session_state["login_email"] = _n(email)
            st.success("Login realizado")
            st.rerun()
        except Exception as e:
            st.error(f"Falha no login: {e}")

def require_auth():
    if allowed_email():
        if current_user_email() != allowed_email():
            login_box(); st.stop()
    else:
        if not current_user_id():
            login_box(); st.stop()
    return current_user_id()
