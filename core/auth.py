# core/auth.py
import streamlit as st
from core.supa import (
    supabase_anon,
    allowed_email,
    save_session_to_file,
    clear_saved_session,
    normalize_session,
)

def _n(email: str) -> str:
    return (email or "").strip().lower()

def current_user():
    # 1) já temos cacheado?
    u = st.session_state.get("sb_user")
    if u:
        return u

    # 2) tentar extrair da sessão normalizada (sb_session)
    sess = st.session_state.get("sb_session")
    if isinstance(sess, dict) and sess.get("user"):
        st.session_state["sb_user"] = sess["user"]
        return sess["user"]

    # 3) fallback robusto: pergunta ao Supabase (se houver cliente com sessão)
    try:
        from core.supa import supabase_user
        sb = supabase_user()  # restaura tokens no cliente
        resp = sb.auth.get_user()
        user_obj = getattr(resp, "user", None) if resp else None
        if user_obj:
            u = {
                "id": getattr(user_obj, "id", None),
                "email": _n(getattr(user_obj, "email", None)),
            }
            st.session_state["sb_user"] = u
            return u
    except Exception:
        pass

    return None

def current_user_email() -> str:
    u = current_user() or {}
    return _n(u.get("email"))

def current_user_id():
    u = current_user() or {}
    return u.get("id")

def logout():
    try:
        supabase_anon().auth.sign_out()
    except Exception:
        pass
    for k in ["sb_session", "sb_user", "login_email"]:
        st.session_state.pop(k, None)
    clear_saved_session()
    st.rerun()

def login_box():
    st.subheader("Entrar no PulseAgenda")
    allowed = allowed_email() or ""
    st.caption("Acesso restrito ao e-mail permitido nas configurações.")
    email = st.text_input("E-mail", value=allowed, disabled=bool(allowed))
    password = st.text_input("Senha", type="password")
    keep = st.checkbox("Manter conectado neste dispositivo", value=True)

    if st.button("Entrar", use_container_width=True):
        if allowed and _n(email) != _n(allowed):
            st.error("E-mail não permitido."); st.stop()

        sb = supabase_anon()
        try:
            res = sb.auth.sign_in_with_password({
                "email": _n(email),
                "password": password
            })

            session = getattr(res, "session", None) or (res.get("session") if isinstance(res, dict) else None)
            user    = getattr(res, "user", None)    or (res.get("user") if isinstance(res, dict) else None)

            if not session:
                st.error("Falha no login: sem sessão retornada."); st.stop()

            norm = normalize_session(session)
            st.session_state["sb_session"] = norm
            st.session_state["sb_user"] = {
                "id": getattr(user, "id", None) if user and not isinstance(user, dict) else (user or {}).get("id"),
                "email": _n(getattr(user, "email", None) if user and not isinstance(user, dict) else (user or {}).get("email")),
            }
            st.session_state["login_email"] = _n(email)

            if keep:
                save_session_to_file(norm)

            st.success("Login realizado")
            st.rerun()
        except Exception as e:
            st.error(f"Falha no login: {e}")

def require_auth():
    """
    Restaura sessão (se existir) e exige autenticação apenas se necessário.
    """
    from core.supa import supabase_user
    supabase_user()  # restaura/normaliza a sessão e tenta preencher sb_user

    if allowed_email():
        if current_user_email() != allowed_email():
            login_box(); st.stop()
    else:
        if not current_user_id():
            login_box(); st.stop()

    return current_user_id()
