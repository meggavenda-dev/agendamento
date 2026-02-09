import streamlit as st
from src.db import tasks_list_by_filters, task_create, task_update

st.header("✅ Tarefas")

col1, col2 = st.columns([1,1])
with col1:
    status = st.selectbox("Status", ["", "Aberta", "Fazendo", "Concluída", "Cancelada"])
with col2:
    clinic_id = st.number_input("Filtrar por clínica (IDCLINICA)", min_value=0, step=1, format="%d")

res = tasks_list_by_filters(status=status or None, clinic_id=int(clinic_id) if clinic_id else None)
tasks = res.data or []

st.subheader("Lista")
if tasks:
    st.dataframe([
        {
            "task_id": t["task_id"],
            "clínica": f"{t.get('clinic_id')} - {(t.get('clinics') or {}).get('legal_name')}",
            "título": t["title"],
            "vencimento": t["due_date"],
            "status": t["status"],
            "prioridade": t["priority"],
        }
        for t in tasks
    ], use_container_width=True)
else:
    st.info("Nenhuma tarefa encontrada.")

st.divider()
st.subheader("Criar tarefa")
with st.form("new_task"):
    new_clinic = st.number_input("Clínica (IDCLINICA)", min_value=1, step=1, format="%d", key="new_clinic")
    title = st.text_input("Título")
    due = st.date_input("Vencimento")
    priority = st.selectbox("Prioridade", [1,2,3], index=1)
    desc = st.text_area("Descrição", height=100)
    ok = st.form_submit_button("Criar", type="primary")
if ok:
    task_create({
        "clinic_id": int(new_clinic),
        "title": title.strip(),
        "due_date": due.isoformat(),
        "priority": int(priority),
        "description": desc.strip() or None
    })
    st.success("Tarefa criada!")
    st.rerun()

st.divider()
st.subheader("Concluir tarefa")
tid = st.number_input("task_id", min_value=1, step=1, format="%d")
if st.button("Marcar como Concluída"):
    task_update(int(tid), {"status": "Concluída"})
    st.success("Concluída!")
    st.rerun()
