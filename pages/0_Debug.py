# pages/00_LoginDebug.py
import streamlit as st
from core.supa import supabase_anon, normalize_session, save_session_to_file
from core.auth import _n

st.set_page_config(page_title="Login Debug", layout="wide")
st.title("Login Debug")

st.caption("Use esta página TEMPORARIAMENTE para diagnosticar o login. Não exibe tokens.")

email = st.text_input("E-mail")
password = st.text_input("Senha", type="password")
keep = st.checkbox("Manter conectado", value=True)

if st.button("Testar login", use_container_width=True):
    sb = supabase_anon()
    try:
        res = sb.auth.sign_in_with_password({"email": _n(email), "password": password})
        # Extrai partes sem dados sensíveis
        session = getattr(res, "session", None) or (res.get("session") if isinstance(res, dict) else None)
        user    = getattr(res, "user", None)    or (res.get("user") if isinstance(res, dict) else None)

        st.subheader("Resposta (sanitizada)")
        st.write({
            "has_session": bool(session),
            "has_user": bool(user),
            "user_id": getattr(user, "id", None) if user and not isinstance(user, dict) else (user or {}).get("id"),
            "user_email": _n(getattr(user, "email", None) if user and not isinstance(user, dict) else (user or {}).get("email")),
        })

        if not session:
            st.error("Supabase não retornou sessão. Verifique credenciais e configurações de Auth.")
        else:
            norm = normalize_session(session)
            st.session_state["sb_session"] = norm
            st.session_state["sb_user"] = {
                "id": getattr(user, "id", None) if user and not isinstance(user, dict) else (user or {}).get("id"),
                "email": _n(getattr(user, "email", None) if user and not isinstance(user, dict) else (user or {}).get("email")),
            }
            if keep:
                save_session_to_file(norm)
            st.success("Login OK — sessão gravada na memória" + (" e em arquivo" if keep else ""))

    except Exception as e:
        # Mostra a mensagem da exceção (o Streamlit pode ofuscar detalhes no Cloud)
        st.error(f"Falha no login: {e!r}")

st.markdown("---")
st.caption("Remova esta página após o diagnóstico.")
