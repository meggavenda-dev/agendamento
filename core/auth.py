import os
import streamlit as st
from core.supa import supabase_anon


def _get(name: str, default: str = "") -> str:
    """Lê configuração por st.secrets (Streamlit Cloud) ou os.environ (local)."""
    if name in st.secrets:
        return str(st.secrets.get(name))
    return os.environ.get(name, default)


def get_redirect_url() -> str:
    """
    Para OTP não é obrigatório, mas é útil se você quiser links
    apontando para seu app (ou no futuro voltar com OAuth).
    """
    return _get("SUPABASE_REDIRECT_URL", "")


def _extract_user_and_upsert_profile(sb, session):
    """Extrai dados do usuário e garante que profile exista."""
    user = getattr(session, "user", None) or (session.get("user") if isinstance(session, dict) else None)
    if not isinstance(user, dict):
        return None

    uid = user.get("id")
    email = user.get("email")
    meta = user.get("user_metadata") or {}

    # Para OTP, user_metadata pode vir vazio. Vamos criar um display_name simples.
    display_name = (
        meta.get("full_name")
        or meta.get("name")
        or (email.split("@")[0] if email else "Usuário")
    )

    if uid:
        sb.table("profiles").upsert({
            "id": uid,
            "email": email,
            "display_name": display_name,
            "theme": "zen",
            "email_notifications": True,
        }).execute()

    return uid


def login_box():
    st.markdown("### Entrar no PulseAgenda")
    st.caption("Use seu e-mail para receber um **código** (OTP) e entrar com segurança.")

    # Mantém o email durante a interação
    email = st.text_input("Seu e-mail", value=st.session_state.get("login_email", ""))

    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("📩 Enviar código", use_container_width=True):
            if not email or "@" not in email:
                st.error("Digite um e-mail válido.")
                st.stop()

            sb = supabase_anon()
            try:
                # Envia código (OTP) para o e-mail
                sb.auth.sign_in_with_otp({"email": email})
                st.session_state["login_email"] = email
                st.success("Código enviado! Verifique seu e-mail.")
            except Exception as e:
                st.error(f"Erro ao enviar código: {e}")

    otp = st.text_input(
        "Código recebido (OTP)",
        value=st.session_state.get("login_otp", ""),
        max_chars=8,
        help="Digite o código enviado pelo Supabase ao seu e-mail."
    )

    with col2:
        if st.button("✅ Entrar", use_container_width=True):
            if not email or "@" not in email:
                st.error("Digite um e-mail válido.")
                st.stop()
            if not otp or len(otp.strip()) < 4:
                st.error("Digite o código recebido.")
                st.stop()

            sb = supabase_anon()
            try:
                # Verifica OTP e cria sessão
                session = sb.auth.verify_otp({
                    "email": email,
                    "token": otp.strip(),
                    "type": "email",
                })
                st.session_state["sb_session"] = session

                # Cria/atualiza profile
                _extract_user_and_upsert_profile(sb, session)

                # limpa campos do login
                st.session_state.pop("login_otp", None)
                st.success("Login realizado ✅")
                st.rerun()
            except Exception as e:
                st.error(f"Código inválido ou expirado: {e}")


def current_user_id():
    session = st.session_state.get("sb_session")
    if not session:
        return None
    user = getattr(session, "user", None) or (session.get("user") if isinstance(session, dict) else None)
    return user.get("id") if isinstance(user, dict) else None


def require_auth():
    uid = current_user_id()
    if not uid:
        login_box()
        st.stop()
    return uid
