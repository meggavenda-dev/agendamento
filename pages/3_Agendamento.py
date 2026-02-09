import streamlit as st
from datetime import datetime, timedelta, date
from dateutil import tz

from src.db import (
    fetch_settings, visits_list_by_date, visits_create, clinics_get_by_id,
    visits_update, visits_delete, clinics_update, clinic_has_any_visit
)
from src.scheduler import build_slots, filter_available_slots, assert_no_conflict

st.header("📅 Agendamento")

cfg = fetch_settings()
tz_name = st.secrets.get("TIMEZONE", "America/Sao_Paulo")
zone = tz.gettz(tz_name)

slot_minutes = int(cfg.get("slot_minutes", 15))
visit_minutes = int(cfg.get("visit_default_minutes", 45))
work_start = cfg.get("work_start", "08:00")
work_end = cfg.get("work_end", "18:00")
cols_in_grid = int(cfg.get("grid_columns", 4))

a, b = st.columns([1, 2])
with a:
    selected_date = st.date_input("Selecione a data", value=date.today())
with b:
    st.caption(f"Grade sugerida: {work_start}–{work_end} | passo {slot_minutes} min | visita {visit_minutes} min")

# Carrega visitas do dia
res = visits_list_by_date(selected_date.isoformat())
visits = res.data or []

existing = []
for v in visits:
    s = datetime.fromisoformat(v["start_at"].replace("Z", "+00:00")).astimezone(zone)
    e = datetime.fromisoformat(v["end_at"].replace("Z", "+00:00")).astimezone(zone)
    existing.append({
        "visit_id": int(v["visit_id"]),
        "start_at": s,
        "end_at": e,
        "status": v["status"],
        "clinic_id": int(v["clinic_id"]),
        "legal_name": (v.get("clinics") or {}).get("legal_name"),
    })

st.subheader("Agendamentos do dia")
if existing:
    st.dataframe([
        {
            "visit_id": x["visit_id"],
            "clínica": f"{x['clinic_id']} - {x['legal_name']}",
            "início": x["start_at"].strftime("%H:%M"),
            "fim": x["end_at"].strftime("%H:%M"),
            "status": x["status"],
        }
        for x in existing
    ], use_container_width=True)
else:
    st.info("Nenhuma visita agendada para esta data.")

# Slots sugeridos
slots = build_slots(selected_date, tz_name, work_start, work_end, slot_minutes, visit_minutes)
available = filter_available_slots(slots, existing)

# Para renderizar a grade, vamos marcar todos os slots e sinalizar ocupados
slot_map = {}
for s, e in slots:
    label = f"{s.strftime('%H:%M')}–{e.strftime('%H:%M')}"
    slot_map[label] = {"start": s, "end": e, "available": False}
for s, e in available:
    label = f"{s.strftime('%H:%M')}–{e.strftime('%H:%M')}"
    if label in slot_map:
        slot_map[label]["available"] = True

st.subheader("Grade de horários sugeridos")
if "selected_slot" not in st.session_state:
    st.session_state.selected_slot = None

labels = list(slot_map.keys())
# Exibe em grid (colunas)
for i in range(0, len(labels), cols_in_grid):
    row = labels[i:i+cols_in_grid]
    cols = st.columns(cols_in_grid)
    for j, lab in enumerate(row):
        info = slot_map[lab]
        is_avail = info["available"]
        is_selected = (st.session_state.selected_slot == lab)

        btn_label = lab
        if not is_avail:
            btn_label += " ⛔"
        elif is_selected:
            btn_label += " ✅"

        clicked = cols[j].button(
            btn_label,
            key=f"slot_{selected_date.isoformat()}_{lab}",
            disabled=not is_avail
        )
        if clicked:
            st.session_state.selected_slot = lab

st.divider()

st.subheader("Criar visita")
mode = st.radio("Modo", ["Sugerido", "Livre"], horizontal=True)
clinic_id = st.number_input("Código da clínica (IDCLINICA)", min_value=1, step=1, format="%d")

start_dt = end_dt = None
if mode == "Sugerido":
    if st.session_state.selected_slot:
        info = slot_map.get(st.session_state.selected_slot)
        if info and info["available"]:
            start_dt, end_dt = info["start"], info["end"]
            st.success(f"Selecionado: {st.session_state.selected_slot}")
    else:
        st.info("Selecione um horário disponível na grade acima.")
else:
    manual_time = st.time_input("Horário de início (livre)", value=datetime.now(zone).time())
    start_dt = datetime.combine(selected_date, manual_time).replace(tzinfo=zone)
    end_dt = start_dt + timedelta(minutes=visit_minutes)

if st.button("Buscar clínica", type="secondary"):
    c = clinics_get_by_id(int(clinic_id)).data
    if not c:
        st.error("Clínica não encontrada. Cadastre/importa primeiro na aba 'Cadastro de Clínicas'.")
    else:
        st.success(f"Clínica: {c['clinic_id']} - {c['legal_name']} | Status: {c.get('status','Prospect')}")

if st.button("Agendar visita", type="primary"):
    if not start_dt or not end_dt:
        st.error("Selecione um horário válido.")
        st.stop()

    # Bloqueia conflito em ambos os modos (segurança)
    try:
        assert_no_conflict(start_dt, end_dt, existing)
    except ValueError as e:
        st.error(str(e))
        st.stop()

    c = clinics_get_by_id(int(clinic_id)).data
    if not c:
        st.error("Clínica não encontrada. Cadastre/importa primeiro.")
        st.stop()

    # Regra (A): ao agendar a PRIMEIRA visita e clínica em Prospect => Em negociação
    had_any = clinic_has_any_visit(int(clinic_id))
    clinic_status = (c.get("status") or "Prospect")

    payload = {
        "clinic_id": int(clinic_id),
        "start_at": start_dt.astimezone(tz.UTC).isoformat(),
        "end_at": end_dt.astimezone(tz.UTC).isoformat(),
        "status": "Agendado",
    }
    visits_create(payload)

    if (not had_any) and clinic_status == "Prospect":
        clinics_update(int(clinic_id), {"status": "Em negociação"})

    st.success("Visita agendada com sucesso!")
    st.session_state.selected_slot = None
    st.rerun()

st.divider()
st.subheader("Ações rápidas (reagendar / excluir)")

if existing:
    visit_ids = [int(x["visit_id"]) for x in existing]
    vid = st.selectbox("Escolha uma visita", visit_ids)

    action = st.selectbox("Ação", ["Reagendar", "Excluir"])

    if action == "Reagendar":
        new_date = st.date_input("Nova data", value=selected_date, key="new_date")
        new_time = st.time_input("Novo horário", value=datetime.now(zone).time(), key="new_time")
        new_start = datetime.combine(new_date, new_time).replace(tzinfo=zone)
        new_end = new_start + timedelta(minutes=visit_minutes)

        if st.button("Confirmar reagendamento"):
            others = [x for x in existing if int(x["visit_id"]) != int(vid)]
            try:
                assert_no_conflict(new_start, new_end, others)
            except ValueError as e:
                st.error(str(e))
                st.stop()

            visits_update(int(vid), {
                "start_at": new_start.astimezone(tz.UTC).isoformat(),
                "end_at": new_end.astimezone(tz.UTC).isoformat(),
                "status": "Reagendada",
            })
            st.success("Visita reagendada!")
            st.rerun()

    if action == "Excluir":
        if st.button("Excluir visita", type="primary"):
            visits_delete(int(vid))
            st.success("Visita excluída!")
            st.rerun()
