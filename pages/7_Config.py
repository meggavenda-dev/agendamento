
import streamlit as st
from core.ui import load_css
from core.auth import require_auth, logout
from core.supa import supabase_user

st.set_page_config(page_title="Config", layout="wide")
load_css(); uid=require_auth(); sb=supabase_user()

st.title("Configuracoes")
with st.sidebar:
    if st.button("Sair", use_container_width=True): logout()

try: prof=sb.table("profiles").select("*").eq("id",uid).single().execute().data
except Exception: prof={}

with st.form("cfg"):
    email_notifications = st.checkbox("Email", value=prof.get("email_notifications", True))
    whatsapp_notifications = st.checkbox("WhatsApp", value=prof.get("whatsapp_notifications", False))
    whatsapp_number = st.text_input("Numero WhatsApp", value=prof.get("whatsapp_number") or "")
    timezone = st.text_input("Fuso horario", value=prof.get("timezone") or "America/Sao_Paulo")
    theme = st.selectbox("Tema", ["zen"], index=0)
    auto_roll = st.checkbox("Mover atrasadas para hoje (06:00)", value=prof.get("auto_rollover_enabled", True))
    auto_bump = st.checkbox("Aumentar prioridade de atrasadas +24h", value=prof.get("auto_bump_priority", True))
    submit=st.form_submit_button("Salvar", use_container_width=True)

if submit:
    payload={"id":uid,"timezone":timezone.strip() or "America/Sao_Paulo","email_notifications":bool(email_notifications),"whatsapp_notifications":bool(whatsapp_notifications),"whatsapp_number":(whatsapp_number.strip() or None),"theme":theme,"auto_rollover_enabled":bool(auto_roll),"auto_bump_priority":bool(auto_bump)}
    try:
        sb.table("profiles").upsert(payload).execute(); st.success("Salvo")
    except Exception as e:
        st.error(f"Erro: {e}")
