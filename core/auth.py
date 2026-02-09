import os
import streamlit as st
from core.supa import supabase_anon


def get_redirect_url() -> str:
    return os.environ.get("SUPABASE_REDIRECT_URL", "")


def login_box():
    st.markdown("### Entrar no PulseAgenda")
    st.caption("Login com Google para manter seus dados sincronizados e seguros.")

    if st.button("Entrar com Google", use_container_width=True):
        sb = supabase_anon()
        redirect_to = get_redirect_url()
        res = sb.auth.sign_in_with_oauth({
            "provider": "google",
            "options": {"redirect_to": redirect_to},
        })
        url = getattr(res, "url", None) or (res.get("url") if isinstance(res, dict) else None)
        if not url:
            st.error("Não consegui gerar a URL de login. Verifique a configuração do Google no Supabase.")
            return
        st.markdown(f"[Clique aqui para continuar o login]({url})")


def handle_oauth_callback():
    # Se a URL tiver ?code=..., troca por sessão e salva em session_state.
    # Também faz upsert em profiles (email/display_name).
    params = st.query_params
    code = params.get("code")
    if not code:
        return

    sb = supabase_anon()
    try:
        session = sb.auth.exchange_code_for_session({"auth_code": code})
        st.session_state["sb_session"] = session

        user = getattr(session, "user", None) or (session.get("user") if isinstance(session, dict) else None)
        if isinstance(user, dict):
            uid = user.get("id")
            email = user.get("email")
            meta = user.get("user_metadata") or {}
            display_name = meta.get("full_name") or meta.get("name") or (email.split("@")[0] if email else "")

            sb.table("profiles").upsert({
                "id": uid,
                "email": email,
                "display_name": display_name,
                "theme": "zen",
                "email_notifications": True,
            }).execute()

        st.query_params.clear()
        st.success("Login realizado ✅")

    except Exception as e:
        st.error(f"Falha no login: {e}")


def current_user_id():
    session = st.session_state.get("sb_session")
    if not session:
        return None
    user = getattr(session, "user", None) or (session.get("user") if isinstance(session, dict) else None)
    return user.get("id") if isinstance(user, dict) else None


def require_auth():
    handle_oauth_callback()
    uid = current_user_id()
    if not uid:
        login_box()
        st.stop()
    return uid
