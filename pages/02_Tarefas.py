import streamlit as st

from db.tasks import list_by_filters
from services.tasks_service import create_task, complete_task

st.header("✅ Tarefas")

col1, col2 = st.columns([1, 1])
with col1:
    status = st.selectbox("Status", ["", "Aberta", "Fazendo", "Concluída", "Cancelada"])
with col2:
    clinic_id = st.number_input("Filtrar por clínica (IDCLINICA)", min_value=0, step=1, format="%d")

_tasks = list_by_filters(status=status or None, clinic_id=int(clinic_id) if clinic_id else None)

st.subheader("Lista")
if _tasks:
    st.dataframe(
        [
            {
                "task_id": t["task_id"],
                "clínica": f"{t.get('clinic_id')} - {(t.get('clinics') or {}).get('legal_name')}",
                "título": t["title"],
                "vencimento": t["due_date"],
                "status": t["status"],
                "prioridade": t.get("priority"),
            }
            for t in _tasks
        ],
        use_container_width=True,
    )
else:
    st.info("Nenhuma tarefa encontrada.")

st.divider()

st.subheader("Criar tarefa")
with st.form("new_task"):
    new_clinic = st.number_input("Clínica (IDCLINICA)", min_value=1, step=1, format="%d", key="new_clinic")
    title = st.text_input("Título")
    due = st.date_input("Vencimento")
    priority = st.selectbox("Prioridade", [1, 2, 3], index=1)
    desc = st.text_area("Descrição", height=100)
    ok = st.form_submit_button("Criar", type="primary")

if ok:
    create_task(
        {
            "clinic_id": int(new_clinic),
            "title": title.strip(),
            "due_date": due.isoformat(),
            "priority": int(priority),
            "description": desc.strip() or None,
        }
    )
    st.success("Tarefa criada!")
    st.rerun()

st.divider()

st.subheader("Concluir tarefa (rápido)")
open_tasks = [t for t in _tasks if t.get("status") not in ("Concluída", "Cancelada")]

if not open_tasks:
    st.info("Nenhuma tarefa aberta para concluir.")
else:
    options = []
    lookup = {}
    for t in open_tasks:
        clinic_name = (t.get("clinics") or {}).get("legal_name", "")
        label = f"#{t['task_id']} | {t['due_date']} | {t['title']} | {t.get('clinic_id')} - {clinic_name}"
        options.append(label)
        lookup[label] = t

    chosen = st.selectbox("Selecione a tarefa", options)
    t = lookup[chosen]

    if st.button("✅ Marcar como Concluída", type="primary"):
        complete_task(int(t["task_id"]))
        st.success("Concluída!")
        st.rerun()
