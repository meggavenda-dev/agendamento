import streamlit as st
from datetime import date

from db.visits import list_by_local_date
from db.tasks import create as task_create
from services.visits_service import update_visit_and_maybe_clinic

st.header("🗂️ Gestão de Visitas")

mode = st.radio("Buscar por", ["Data", "Clínica (em breve)"], horizontal=True)

if mode == "Data":
    d = st.date_input("Data", value=date.today())
    tz_name = st.secrets.get("TIMEZONE", "America/Sao_Paulo")
    visits = list_by_local_date(d, tz_name)

    if not visits:
        st.info("Nenhuma visita nessa data.")
        st.stop()

    options = [f"#{v['visit_id']} - {v['clinic_id']} - {(v.get('clinics') or {}).get('legal_name')}" for v in visits]
    chosen = st.selectbox("Escolha a visita", options)
    v = visits[options.index(chosen)]

    st.subheader("Registro da visita")
    with st.form("visit_notes"):
        summary = st.text_input("Resumo curto", value=v.get("summary") or "")
        discussion = st.text_area("O que foi debatido (MVP)", value=v.get("discussion_rich") or "", height=220)
        next_steps = st.text_area("Próximos passos", value=v.get("next_steps") or "", height=140)

        status_options = ["Agendado", "Realizado", "Reagendada", "Fechado Parceria", "Sem Parceria"]
        status = st.selectbox(
            "Status",
            status_options,
            index=status_options.index(v["status"]) if v.get("status") in status_options else 0,
        )

        saved = st.form_submit_button("Salvar", type="primary")

    if saved:
        update_visit_and_maybe_clinic(
            int(v["visit_id"]),
            int(v["clinic_id"]),
            {
                "summary": summary.strip() or None,
                "discussion_rich": discussion.strip() or None,
                "next_steps": next_steps.strip() or None,
                "status": status,
            },
        )
        st.success("Visita atualizada!")
        st.rerun()

    st.divider()
    st.subheader("Criar tarefa decorrente desta visita")

    with st.form("task_from_visit"):
        title = st.text_input("Título da tarefa")
        due = st.date_input("Vencimento", value=d)
        desc = st.text_area("Descrição", height=80)
        ok = st.form_submit_button("Criar tarefa", type="secondary")

    if ok:
        task_create(
            {
                "clinic_id": int(v["clinic_id"]),
                "visit_id": int(v["visit_id"]),
                "title": title.strip(),
                "due_date": due.isoformat(),
                "description": desc.strip() or None,
            }
        )
        st.success("Tarefa criada e vinculada à visita!")
        st.rerun()

else:
    st.info("Busca por clínica será adicionada na próxima iteração (histórico completo por IDCLINICA).")
