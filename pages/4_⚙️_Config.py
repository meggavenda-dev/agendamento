import streamlit as st
from core.auth import require_auth
from core.supa import supabase_anon
from core.ui import load_css

st.set_page_config(page_title="Config • PulseAgenda", layout="wide")
load_css()

uid = require_auth()
sb = supabase_anon()

st.title("⚙️ Configurações")
st.caption("Tema Zen e notificações.")

try:
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
    sb.table("profiles").upsert({
        "id": uid,
        "timezone": timezone.strip() or "America/Sao_Paulo",
        "email_notifications": email_notifications,
        "whatsapp_notifications": whatsapp_notifications,
        "whatsapp_number": whatsapp_number.strip() if whatsapp_number.strip() else None,
        "theme": theme,
    }).execute()

    st.success("Configurações salvas ✅")
