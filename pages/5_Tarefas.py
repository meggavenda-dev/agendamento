# -*- coding: utf-8 -*-
import streamlit as st
from src.db import tasks_list_by_filters, tasks_list_without_due, task_create, task_update
from src.constants import TASK_STATUSES, IMPACT_LEVELS

st.header("Tarefas")

col1, col2, col3 = st.columns([1,1,1])
with col1:
    status = st.selectbox("Status", [""] + TASK_STATUSES)
with col2:
    clinic_id = st.number_input("Filtrar por clínica (IDCLINICA)", min_value=0, step=1, format="%d")
with col3:
    only_critical = st.checkbox("Somente críticas", value=False)

res = tasks_list_by_filters(status=status or None, clinic_id=int(clinic_id) if clinic_id else None, only_critical=only_critical)
tasks = res.data or []

st.subheader("Lista")
if tasks:
    st.dataframe([
        {
            "task_id": t["task_id"],
            "clinica": f"{t.get('clinic_id')} - {(t.get('clinics') or {}).get('legal_name')}",
            "titulo": t.get("title"),
            "vencimento": t.get("due_date"),
            "status": t.get("status"),
            "prioridade": t.get("priority"),
            "impacto": t.get("impact"),
        }
        for t in tasks
    ], use_container_width=True)
else:
    st.info("Nenhuma tarefa encontrada.")

st.divider()

st.subheader("Tarefas sem prazo")
no_due = (tasks_list_without_due().data or [])
if no_due:
    st.dataframe([
        {
            "task_id": t["task_id"],
            "clinica": (t.get("clinics") or {}).get("legal_name"),
            "titulo": t.get("title"),
            "status": t.get("status"),
            "prioridade": t.get("priority"),
        }
        for t in no_due
    ], use_container_width=True)
else:
    st.success("Nenhuma tarefa sem prazo ✅")

st.divider()

st.subheader("Criar tarefa")
with st.form("new_task"):
    new_clinic = st.number_input("Clínica (IDCLINICA)", min_value=1, step=1, format="%d")
    title = st.text_input("Título")
    due = st.date_input("Vencimento")
    priority = st.selectbox("Prioridade", [1,2,3], index=1)
    impact = st.selectbox("Impacto", IMPACT_LEVELS, index=1)
    desc = st.text_area("Descrição", height=100)
    ok = st.form_submit_button("Criar", type="primary")

if ok:
    task_create({
        "clinic_id": int(new_clinic),
        "title": title.strip(),
        "due_date": due.isoformat(),
        "priority": int(priority),
        "impact": impact,
        "status": "Pendente",
        "description": desc.strip() or None,
    })
    st.success("Criada!")
    st.rerun()

st.divider()

st.subheader("Atualizar status")
tid = st.number_input("task_id", min_value=1, step=1, format="%d")
new_status = st.selectbox("Novo status", TASK_STATUSES, index=2)
if st.button("Aplicar"):
    task_update(int(tid), {"status": new_status})
    st.success("Atualizado!")
    st.rerun()
