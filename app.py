# -*- coding: utf-8 -*-
import streamlit as st
from src.db import fetch_settings

st.set_page_config(page_title="Captação de Clínicas — CRM", layout="wide")
st.title("Captação de Clínicas — CRM de Conversão")

cfg = fetch_settings()
with st.expander("Configurações (scheduler)", expanded=False):
    st.json(cfg)

st.markdown("""
### Como usar
- Use o menu lateral para acessar: **Hoje**, **Funil**, **Agendamento**, **Gestão de Visitas**, **Tarefas**, **Clínicas** e **Relatórios**.
- O objetivo do sistema é responder diariamente:
  1) **Onde devo ir hoje?**
  2) **Em quem devo focar?**
  3) **O que está travando o fechamento?**
""")

st.info("MVP pronto para operação + priorização + funil + alertas. Para produção, recomendo autenticação e RLS.")
