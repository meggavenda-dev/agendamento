import streamlit as st
from core.supa import supabase_anon, supabase_user, allowed_email


def _normalize_email(email: str) -> str:
    return (email or "").strip().lower()


def current_user():
    """
    Retorna usuário (objeto ou dict) se logado.
    """
    user = st.session_state.get("sb_user")
    if user:
        return user

    sess = st.session_state.get("sb_session")
    if not sess:
        return None

    # algumas versões guardam user dentro da session
    return getattr(sess, "user", None) or (sess.get("user") if isinstance(sess, dict) else None)


def current_user_email() -> str:
    user = current_user()
    email = getattr(user, "email", None) if user else None
    if not email and isinstance(user, dict):
        email = user.get("email")
    return _normalize_email(email)


def current_user_id():
    user = current_user()
    uid = getattr(user, "id", None) if user else None
    if not uid and isinstance(user, dict):
        uid = user.get("id")
    return uid


def logout():
    try:
        sb = supabase_anon()
        sb.auth.sign_out()
    except Exception:
        pass

    for k in ["sb_session", "sb_user", "login_email"]:
        st.session_state.pop(k, None)

    st.rerun()


def _ensure_profile_exists():
    """
    Garante que exista uma linha em public.profiles para o usuário logado.
    IMPORTANTE: precisa usar supabase_user() para respeitar RLS.
    """
    uid = current_user_id()
    email = current_user_email()
    if not uid or not email:
        return

    # monta display_name simples
    display_name = email.split("@")[0] if "@" in email else "Usuário"

    sb = supabase_user()
    # Upsert do perfil do próprio usuário
    sb.table("profiles").upsert(
        {
            "id": uid,
            "email": email,
            "display_name": display_name,
            "theme": "zen",
            "email_notifications": True,
        }
    ).execute()


def login_box():
    st.markdown("### Entrar no PulseAgenda")
    st.caption("Acesso restrito ao proprietário do app (login com senha).")

    allowed = allowed_email()
    st.info(f"✅ Somente o e-mail **{allowed}** pode acessar.")

    # Você pode deixar o e-mail fixo (sem chance de erro):
    email = st.text_input("E-mail", value=allowed, disabled=True)
    password = st.text_input("Senha", type="password", help="Digite a senha cadastrada no Supabase Auth.")

    if st.button("✅ Entrar", use_container_width=True):
        email_n = _normalize_email(email)

        if email_n != allowed:
            st.error("Acesso negado: e-mail não permitido.")
            st.stop()

        if not password or len(password) < 6:
            st.error("Digite uma senha válida (mínimo recomendado: 6 caracteres).")
            st.stop()

        sb = supabase_anon()
        try:
            # Login com email+senha (Supabase Auth). [2](https://supabase.com/docs/reference/python/auth-signinwithpassword)
            res = sb.auth.sign_in_with_password({"email": email_n, "password": password})  # [2](https://supabase.com/docs/reference/python/auth-signinwithpassword)

            session = getattr(res, "session", None) or (res.get("session") if isinstance(res, dict) else None)
            user = getattr(res, "user", None) or (res.get("user") if isinstance(res, dict) else None)

            # defesa extra: se por algum motivo retornasse user de outro email
            u_email = getattr(user, "email", None) if user else None
            if not u_email and isinstance(user, dict):
                u_email = user.get("email")

            if _normalize_email(u_email) != allowed:
                sb.auth.sign_out()
                st.error("Acesso negado.")
                st.stop()

            # persiste em session_state
            st.session_state["sb_session"] = session
            st.session_state["sb_user"] = user
            st.session_state["login_email"] = email_n

            # cria/atualiza profile (com client logado)
            _ensure_profile_exists()

            st.success("Login realizado ✅")
            st.rerun()

        except Exception as e:
            st.error(f"Falha no login: {e}")


def require_auth():
    """
    Use no topo das páginas.
    Se não logado (ou não for o e-mail permitido), mostra login_box e interrompe.
    """
    if current_user_email() != allowed_email():
        login_box()
        st.stop()

    return current_user_id()
