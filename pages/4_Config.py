import streamlit as st
from core.auth import require_auth, logout
from core.supa import supabase_user
from core.ui import load_css

st.set_page_config(page_title="Config • PulseAgenda", layout="wide")
load_css()

uid = require_auth()

# ✅ MUITO IMPORTANTE:
# Use o client "logado" para respeitar RLS e não dar PostgREST APIError.
sb = supabase_user()

st.title("⚙️ Configurações")
st.caption("Tema Zen e notificações.")

# Botão opcional de sair
with st.sidebar:
    if st.button("Sair", use_container_width=True):
        logout()

# Carrega profile com segurança
try:
    # Se existir 1 linha, traz. Se não existir, cai no except e cria defaults
    prof = sb.table("profiles").select("*").eq("id", uid).single().execute().data
except Exception:
    prof = {}

with st.form("cfg"):
    st.subheader("Notificações")
    email_notifications = st.checkbox("E-mail (Gmail)", value=prof.get("email_notifications", True))
    whatsapp_notifications = st.checkbox("WhatsApp (Twilio Sandbox)", value=prof.get("whatsapp_notifications", False))

    st.caption("Formato recomendado para WhatsApp: +55DDDNUMERO (ex: +5561999999999)")
    whatsapp_number = st.text_input("Seu número WhatsApp", value=prof.get("whatsapp_number") or "")

    st.subheader("Preferências")
    timezone = st.text_input("Fuso horário", value=prof.get("timezone") or "America/Sao_Paulo")
    theme = st.selectbox("Tema", ["zen"], index=0)

    salvar = st.form_submit_button("Salvar", use_container_width=True)

if salvar:
    payload = {
        "id": uid,
        "timezone": (timezone.strip() or "America/Sao_Paulo"),
        "email_notifications": bool(email_notifications),
        "whatsapp_notifications": bool(whatsapp_notifications),
        "whatsapp_number": (whatsapp_number.strip() if whatsapp_number.strip() else None),
        "theme": theme,
    }

    try:
        sb.table("profiles").upsert(payload).execute()
        st.success("Configurações salvas ✅")
    except Exception as e:
        st.error(f"Erro ao salvar configurações: {e}")
