import streamlit as st
from db.settings import fetch_settings

st.set_page_config(page_title="Captação de Clínicas", layout="wide")
st.title("📌 Captação de Clínicas - CRM de Visitas")

cfg = fetch_settings()
with st.expander("⚙️ Configurações atuais (scheduler)", expanded=False):
    st.json(cfg)

st.info("Use o menu lateral para acessar: Hoje, Tarefas, Agendamento, Gestão de Visitas e Cadastro de Clínicas.")
