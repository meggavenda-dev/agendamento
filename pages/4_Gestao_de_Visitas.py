# -*- coding: utf-8 -*-
import streamlit as st
from datetime import date, datetime
from dateutil import tz

from src.db import (
    visits_list_by_date,
    visits_list_by_clinic,
    visits_update,
    task_create,
    apply_clinic_status_from_visit,
    participants_list,
    participant_add,
    participant_delete,
)
from src.constants import VISIT_STATUSES, IMPACT_LEVELS

st.header("Gestão de Visitas")

mode = st.radio("Buscar por", ["Data", "Clínica"], horizontal=True)

tz_name = st.secrets.get("TIMEZONE", "America/Sao_Paulo")
zone = tz.gettz(tz_name)

visits = []
if mode == "Data":
    d = st.date_input("Data", value=date.today())
    visits = (visits_list_by_date(d.isoformat()).data or [])
else:
    clinic_id = st.number_input("Clínica (IDCLINICA)", min_value=1, step=1, format="%d")
    if st.button("Buscar"):
        visits = (visits_list_by_clinic(int(clinic_id)).data or [])

if not visits:
    st.info("Nenhuma visita encontrada.")
    st.stop()

options, lookup = [], {}
for v in visits:
    s = datetime.fromisoformat(v["start_at"].replace("Z", "+00:00")).astimezone(zone)
    label = f"#{v['visit_id']} | {s.strftime('%d/%m %H:%M')} | Clínica {v['clinic_id']}"
    options.append(label)
    lookup[label] = v

chosen = st.selectbox("Escolha a visita", options)
v = lookup[chosen]

st.subheader("Registro")
with st.form("visit_form"):
    c1, c2 = st.columns([1,1])
    with c1:
        summary = st.text_input("Resumo curto", value=v.get("summary") or "")
        objective = st.text_input("Objetivo", value=v.get("objective") or "")
    with c2:
        visit_type = st.text_input("Tipo", value=v.get("visit_type") or "")
        ata_finalized = st.checkbox("Ata finalizada", value=bool(v.get("ata_finalized")))

    discussion = st.text_area("Debate", value=v.get("discussion_rich") or "", height=240)
    next_steps = st.text_area("Próximos passos", value=v.get("next_steps") or "", height=140)

    status = st.selectbox(
        "Status",
        VISIT_STATUSES,
        index=VISIT_STATUSES.index(v.get("status")) if v.get("status") in VISIT_STATUSES else 0,
    )

    saved = st.form_submit_button("Salvar", type="primary")

if saved:
    visits_update(int(v["visit_id"]), {
        "summary": summary.strip() or None,
        "objective": objective.strip() or None,
        "visit_type": visit_type.strip() or None,
        "discussion_rich": discussion.strip() or None,
        "next_steps": next_steps.strip() or None,
        "ata_finalized": bool(ata_finalized),
        "status": status,
    })
    apply_clinic_status_from_visit(int(v["clinic_id"]), status)
    st.success("Atualizado!")
    st.rerun()

st.divider()

st.subheader("Participantes")
plist = (participants_list(int(v["visit_id"])).data or [])
if plist:
    st.dataframe([
        {
            "participant_id": p["participant_id"],
            "nome": p.get("name"),
            "cargo": p.get("title"),
            "papel": p.get("decision_role"),
            "influencia": p.get("influence"),
        }
        for p in plist
    ], use_container_width=True)
else:
    st.info("Sem participantes cadastrados.")

with st.form("add_participant"):
    c1, c2, c3 = st.columns([2,1,1])
    with c1:
        name = st.text_input("Nome")
        title = st.text_input("Cargo")
    with c2:
        influence = st.selectbox("Influência", ["Baixa", "Média", "Alta"], index=1)
    with c3:
        decision_role = st.selectbox("Papel", ["Decisor", "Influenciador", "Operacional"], index=1)
    ok = st.form_submit_button("Adicionar")

if ok:
    participant_add({
        "visit_id": int(v["visit_id"]),
        "name": name.strip(),
        "title": title.strip() or None,
        "influence": influence,
        "decision_role": decision_role,
    })
    st.success("Participante adicionado!")
    st.rerun()

pid = st.number_input("Remover participant_id", min_value=0, step=1)
if pid and st.button("Remover"):
    participant_delete(int(pid))
    st.success("Removido.")
    st.rerun()

st.divider()

st.subheader("Tarefa decorrente")
with st.form("task_from_visit"):
    ttitle = st.text_input("Título")
    due = st.date_input("Vencimento", value=date.today())
    impact = st.selectbox("Impacto", IMPACT_LEVELS, index=1)
    desc = st.text_area("Descrição", height=80)
    ok2 = st.form_submit_button("Criar tarefa")

if ok2:
    task_create({
        "clinic_id": int(v["clinic_id"]),
        "visit_id": int(v["visit_id"]),
        "title": ttitle.strip(),
        "due_date": due.isoformat(),
        "description": desc.strip() or None,
        "impact": impact,
        "status": "Pendente",
        "priority": 2,
    })
    st.success("Tarefa criada!")
    st.rerun()
