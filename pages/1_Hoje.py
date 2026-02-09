# -*- coding: utf-8 -*-
import streamlit as st
from datetime import datetime, timedelta
from dateutil import tz

from src.db import (
    visits_list_range,
    tasks_list_overdue,
    visits_update,
    apply_clinic_status_from_visit,
    clinics_without_next_action,
    visits_realized_without_minutes,
    clinics_hot,
)

st.header("Hoje — Painel de Guerra")

tz_name = st.secrets.get("TIMEZONE", "America/Sao_Paulo")
zone = tz.gettz(tz_name)
now = datetime.now(zone)
start_today = now.replace(hour=0, minute=0, second=0, microsecond=0)
end_plus3 = (start_today + timedelta(days=3)).replace(hour=23, minute=59, second=59, microsecond=0)

today_iso = now.date().isoformat()

# Visitas hoje + próximos 3 dias
vis_res = visits_list_range(
    start_today.astimezone(tz.UTC).isoformat(),
    end_plus3.astimezone(tz.UTC).isoformat(),
)
visits = vis_res.data or []

st.subheader("Visitas (Hoje + próximos 3 dias)")
if not visits:
    st.info("Sem visitas no período.")
else:
    rows, options, lookup = [], [], {}
    for v in visits:
        s = datetime.fromisoformat(v["start_at"].replace("Z", "+00:00")).astimezone(zone)
        e = datetime.fromisoformat(v["end_at"].replace("Z", "+00:00")).astimezone(zone)
        clinic_name = (v.get("clinics") or {}).get("legal_name")
        opt = f"#{v['visit_id']} | {s.strftime('%d/%m %H:%M')} | {v['clinic_id']} - {clinic_name} | {v['status']}"
        options.append(opt)
        lookup[opt] = v
        rows.append({
            "visit_id": int(v["visit_id"]),
            "data": s.strftime("%d/%m/%Y"),
            "inicio": s.strftime("%H:%M"),
            "fim": e.strftime("%H:%M"),
            "clinica": f"{v['clinic_id']} - {clinic_name}",
            "status": v.get("status"),
            "tipo": v.get("visit_type"),
            "objetivo": v.get("objective"),
        })
    st.dataframe(rows, use_container_width=True)

    st.markdown("### Ação rápida")
    chosen = st.selectbox("Selecione a visita", options)
    v = lookup[chosen]

    status_list = ["Agendado", "Confirmada", "Realizado", "Reagendada", "Cancelada", "Fechado Parceria", "Sem Parceria"]
    new_status = st.selectbox(
        "Atualizar status para",
        status_list,
        index=status_list.index(v.get("status")) if v.get("status") in status_list else 0,
    )

    if st.button("Atualizar status", type="primary"):
        visits_update(int(v["visit_id"]), {"status": new_status})
        apply_clinic_status_from_visit(int(v["clinic_id"]), new_status)
        st.success("Status atualizado!")
        st.rerun()

st.divider()

# Alertas
colA, colB, colC = st.columns(3)

with colA:
    st.subheader("Clínicas sem próxima ação")
    res = clinics_without_next_action().data or []
    if res:
        st.dataframe([
            {
                "clinic_id": x["clinic_id"],
                "clinica": x["legal_name"],
                "etapa": x.get("lead_status"),
                "interesse": x.get("interest_level"),
                "prob": x.get("probability"),
            }
            for x in res
        ], use_container_width=True, height=260)
    else:
        st.success("Tudo com próxima ação definida ✅")

with colB:
    st.subheader("Realizadas sem ata finalizada")
    res = visits_realized_without_minutes().data or []
    if res:
        st.dataframe([
            {
                "visit_id": x["visit_id"],
                "clinica": (x.get("clinics") or {}).get("legal_name"),
                "data": x.get("start_at"),
                "ata_finalizada": x.get("ata_finalized"),
            }
            for x in res
        ], use_container_width=True, height=260)
    else:
        st.success("Nenhuma pendência de ata 🎉")

with colC:
    st.subheader("Clínicas quentes")
    res = clinics_hot().data or []
    if res:
        st.dataframe([
            {
                "clinic_id": x["clinic_id"],
                "clinica": x["legal_name"],
                "etapa": x.get("lead_status"),
                "prob": x.get("probability"),
                "potencial": x.get("potential_value"),
                "prox_acao": x.get("next_action"),
                "prazo": x.get("next_action_due"),
            }
            for x in res
        ], use_container_width=True, height=260)
    else:
        st.info("Sem clínicas quentes no momento.")

st.divider()

# Tarefas vencidas
st.subheader("Tarefas vencidas")
overdue = (tasks_list_overdue(today_iso).data or [])
if overdue:
    st.dataframe([
        {
            "task_id": t["task_id"],
            "clinica": (t.get("clinics") or {}).get("legal_name"),
            "titulo": t.get("title"),
            "vencimento": t.get("due_date"),
            "status": t.get("status"),
            "prioridade": t.get("priority"),
            "impacto": t.get("impact"),
        }
        for t in overdue
    ], use_container_width=True)
else:
    st.success("Nenhuma tarefa vencida 🎉")
