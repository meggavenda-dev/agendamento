import streamlit as st
from core.supa import supabase_anon, allowed_email, save_session_to_file, clear_saved_session

def _n(email: str) -> str:
    return (email or "").strip().lower()

def logout():
    try:
        supabase_anon().auth.sign_out()
    except Exception:
        pass
    for k in ["sb_session","sb_user","login_email"]:
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
            res = sb.auth.sign_in_with_password({"email": _n(email), "password": password})
            session = getattr(res, "session", None) or (res.get("session") if isinstance(res, dict) else None)
            user    = getattr(res, "user", None)    or (res.get("user") if isinstance(res, dict) else None)
            if not session:
                st.error("Falha no login: sem sessão retornada."); st.stop()

            st.session_state["sb_session"] = session
            st.session_state["sb_user"] = user
            st.session_state["login_email"] = _n(email)

            # >>> Persistência local no servidor
            if keep:
                save_session_to_file(session)

            st.success("Login realizado")
            st.rerun()
        except Exception as e:
            st.error(f"Falha no login: {e}")
