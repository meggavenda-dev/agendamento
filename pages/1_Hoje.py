# -*- coding: utf-8 -*-
import streamlit as st
from datetime import datetime, timedelta
from dateutil import tz

from src.style import apply_style, card_open, card_close
from src.db import (
    visits_list_range,
    tasks_list_overdue,
    visits_update,
    apply_clinic_status_from_visit,
    clinics_without_next_action,
    visits_realized_without_minutes,
    clinics_hot,
)

apply_style()

st.title("📍 Hoje")
st.caption("Painel de guerra: foco no que move fechamento e elimina pendências.")

tz_name = st.secrets.get("TIMEZONE", "America/Sao_Paulo")
zone = tz.gettz(tz_name)
now = datetime.now(zone)
start_today = now.replace(hour=0, minute=0, second=0, microsecond=0)
end_plus3 = (start_today + timedelta(days=3)).replace(hour=23, minute=59, second=59, microsecond=0)

today_iso = now.date().isoformat()

vis_res = visits_list_range(
    start_today.astimezone(tz.UTC).isoformat(),
    end_plus3.astimezone(tz.UTC).isoformat(),
)
visits = vis_res.data or []

# KPIs
vis_today = 0
for v in visits:
    s = datetime.fromisoformat(v["start_at"].replace("Z", "+00:00")).astimezone(zone)
    if s.date() == now.date():
        vis_today += 1

kpi1, kpi2, kpi3, kpi4 = st.columns(4)
with kpi1:
    st.metric("Visitas hoje", vis_today)
with kpi2:
    st.metric("Próx 3 dias", len(visits))

od = (tasks_list_overdue(today_iso).data or [])
with kpi3:
    st.metric("Tarefas vencidas", len(od))

no_next = (clinics_without_next_action().data or [])
with kpi4:
    st.metric("Sem próxima ação", len(no_next))

st.divider()

# Visitas tabela + ação rápida
left, right = st.columns([2,1])

with left:
    st.subheader("Agenda (Hoje + 3 dias)")
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
                "data": s.strftime("%d/%m"),
                "início": s.strftime("%H:%M"),
                "fim": e.strftime("%H:%M"),
                "clínica": clinic_name,
                "status": v.get("status"),
                "tipo": v.get("visit_type"),
            })
        st.dataframe(rows, use_container_width=True, height=360)

with right:
    st.subheader("Ação rápida")
    if visits:
        chosen = st.selectbox("Selecione a visita", options)
        v = lookup[chosen]
        status_list = ["Agendado", "Confirmada", "Realizado", "Reagendada", "Cancelada", "Fechado Parceria", "Sem Parceria"]
        new_status = st.selectbox(
            "Atualizar status",
            status_list,
            index=status_list.index(v.get("status")) if v.get("status") in status_list else 0,
        )
        if st.button("Salvar status", type="primary", use_container_width=True):
            visits_update(int(v["visit_id"]), {"status": new_status})
            apply_clinic_status_from_visit(int(v["clinic_id"]), new_status)
            st.success("Atualizado!")
            st.rerun()
    else:
        st.info("Sem visita para atualizar.")

st.divider()

# Alert cards
c1, c2, c3 = st.columns(3)

with c1:
    card_open()
    st.markdown("<div class='card-title'>🔴 Clínicas sem próxima ação</div>", unsafe_allow_html=True)
    st.markdown("<div class='muted'>Leads em andamento que estão parados.</div>", unsafe_allow_html=True)
    if not no_next:
        st.success("Tudo definido ✅")
    else:
        for x in no_next[:8]:
            st.write(f"**{x['clinic_id']} — {x['legal_name']}**")
        with st.expander("Ver tudo"):
            st.dataframe(no_next, use_container_width=True)
    card_close()

with c2:
    card_open()
    st.markdown("<div class='card-title'>🟡 Realizadas sem ata finalizada</div>", unsafe_allow_html=True)
    st.markdown("<div class='muted'>Visitas que precisam virar registro/decisão.</div>", unsafe_allow_html=True)
    res = visits_realized_without_minutes().data or []
    if not res:
        st.success("Nada pendente ✅")
    else:
        for x in res[:8]:
            clinic = (x.get("clinics") or {}).get("legal_name")
            st.write(f"**#{x['visit_id']} — {clinic}**")
        with st.expander("Ver tudo"):
            st.dataframe(res, use_container_width=True)
    card_close()

with c3:
    card_open()
    st.markdown("<div class='card-title'>🟢 Clínicas quentes</div>", unsafe_allow_html=True)
    st.markdown("<div class='muted'>Alta chance/alto interesse.</div>", unsafe_allow_html=True)
    hot = (clinics_hot().data or [])
    if not hot:
        st.info("Sem quentes agora")
    else:
        for x in hot[:8]:
            st.write(f"**{x['clinic_id']} — {x['legal_name']}** | prob: {x.get('probability')}")
        with st.expander("Ver tudo"):
            st.dataframe(hot, use_container_width=True)
    card_close()

st.divider()

st.subheader("Tarefas vencidas")
if od:
    st.dataframe(od, use_container_width=True, height=260)
else:
    st.success("Nenhuma vencida 🎉")
