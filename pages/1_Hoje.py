# -*- coding: utf-8 -*-
import streamlit as st
from datetime import datetime, timedelta, date
from dateutil import tz

from src.style import apply_style, card_open, card_close
from src.db import fetch_settings, visits_list_by_date, visits_create, clinics_get_by_id, clinics_update
from src.scheduler import build_slots, filter_available_slots, assert_no_conflict
from src.constants import VISIT_TYPES

apply_style()

st.title("📅 Agendamento")
st.caption("Marque visitas com rapidez e sem conflitos.")

cfg = fetch_settings()
tz_name = st.secrets.get("TIMEZONE", "America/Sao_Paulo")
zone = tz.gettz(tz_name)
slot_minutes = int(cfg.get("slot_minutes", 15))
visit_minutes_default = int(cfg.get("visit_default_minutes", 45))
work_start = cfg.get("work_start", "08:00")
work_end = cfg.get("work_end", "18:00")
cols_in_grid = int(cfg.get("grid_columns", 4))

cA, cB = st.columns([1,2])
with cA:
    selected_date = st.date_input("Data", value=date.today())
with cB:
    st.markdown(f"<span class='muted'>Janela: {work_start}–{work_end} • passo {slot_minutes}min • padrão {visit_minutes_default}min</span>", unsafe_allow_html=True)

res = visits_list_by_date(selected_date.isoformat())
visits = res.data or []
existing = []
for v in visits:
    s = datetime.fromisoformat(v["start_at"].replace("Z", "+00:00")).astimezone(zone)
    e = datetime.fromisoformat(v["end_at"].replace("Z", "+00:00")).astimezone(zone)
    existing.append({"visit_id": int(v["visit_id"]), "start_at": s, "end_at": e})

card_open()
st.markdown("<div class='card-title'>Agenda do dia</div>", unsafe_allow_html=True)
if visits:
    st.dataframe([
        {"início": datetime.fromisoformat(v["start_at"].replace("Z", "+00:00")).astimezone(zone).strftime("%H:%M"),
         "clínica": (v.get("clinics") or {}).get("legal_name"),
         "status": v.get("status")}
        for v in visits
    ], use_container_width=True, height=220)
else:
    st.info("Sem visitas nesse dia.")
card_close()

slots = build_slots(selected_date, tz_name, work_start, work_end, slot_minutes, visit_minutes_default)
available = filter_available_slots(slots, existing)
slot_map = {f"{s.strftime('%H:%M')}–{e.strftime('%H:%M')}": {"start": s, "end": e, "available": False} for s,e in slots}
for s,e in available:
    slot_map[f"{s.strftime('%H:%M')}–{e.strftime('%H:%M')}"]["available"] = True

st.subheader("Horários disponíveis")
if "selected_slot" not in st.session_state:
    st.session_state.selected_slot = None
labels = list(slot_map.keys())
for i in range(0, len(labels), cols_in_grid):
    row = labels[i:i+cols_in_grid]
    cols = st.columns(cols_in_grid)
    for j, lab in enumerate(row):
        info = slot_map[lab]
        label = lab + (" ✅" if st.session_state.selected_slot==lab else "")
        if cols[j].button(label, key=f"slot_{selected_date}_{lab}", disabled=not info["available"]):
            st.session_state.selected_slot = lab
            st.rerun()

st.divider()

st.subheader("Criar visita")
clinic_id = st.number_input("IDCLINICA", min_value=1, step=1)
visit_type = st.selectbox("Tipo", VISIT_TYPES)
duration = st.number_input("Duração (min)", min_value=15, step=5, value=visit_minutes_default)
objective = st.text_input("Objetivo (obrigatório)")

if st.button("Agendar", type="primary"):
    if not st.session_state.selected_slot:
        st.error("Selecione um horário")
        st.stop()
    if not objective.strip():
        st.error("Objetivo é obrigatório")
        st.stop()
    c = clinics_get_by_id(int(clinic_id))
    if not c:
        st.error("Clínica não encontrada")
        st.stop()
    start_dt = slot_map[st.session_state.selected_slot]["start"]
    end_dt = start_dt + timedelta(minutes=int(duration))
    assert_no_conflict(start_dt, end_dt, existing)
    visits_create({
        "clinic_id": int(clinic_id),
        "start_at": start_dt.astimezone(tz.UTC).isoformat(),
        "end_at": end_dt.astimezone(tz.UTC).isoformat(),
        "status": "Agendado",
        "visit_type": visit_type,
        "objective": objective.strip(),
        "duration_minutes": int(duration)
    })
    if (c.get("lead_status") or "Novo") == "Novo":
        clinics_update(int(clinic_id), {"lead_status": "Em contato"})
    st.success("Agendado!")
    st.session_state.selected_slot = None
    st.rerun()
