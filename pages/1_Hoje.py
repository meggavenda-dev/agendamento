import streamlit as st
from datetime import datetime, timedelta
from dateutil import tz

from src.db import visits_list_range, tasks_list_overdue, visits_update, apply_clinic_status_from_visit

st.header("📍 Hoje")

tz_name = st.secrets.get("TIMEZONE", "America/Sao_Paulo")
zone = tz.gettz(tz_name)
now = datetime.now(zone)

start_today = now.replace(hour=0, minute=0, second=0, microsecond=0)
end_plus3 = (start_today + timedelta(days=3)).replace(hour=23, minute=59, second=59, microsecond=0)

vis_res = visits_list_range(
    start_today.astimezone(tz.UTC).isoformat(),
    end_plus3.astimezone(tz.UTC).isoformat()
)
visits = vis_res.data or []

today_iso = now.date().isoformat()
overdue = (tasks_list_overdue(today_iso).data or [])

st.subheader("Visitas (Hoje + próximos 3 dias)")

if not visits:
    st.info("Sem visitas no período.")
else:
    # Monta linhas e opções
    rows = []
    options = []
    visit_lookup = {}
    for v in visits:
        s = datetime.fromisoformat(v["start_at"].replace("Z", "+00:00")).astimezone(zone)
        e = datetime.fromisoformat(v["end_at"].replace("Z", "+00:00")).astimezone(zone)
        clinic_name = (v.get("clinics") or {}).get("legal_name")
        opt = f"#{v['visit_id']} | {s.strftime('%d/%m %H:%M')} | {v['clinic_id']} - {clinic_name} | {v['status']}"
        options.append(opt)
        visit_lookup[opt] = v
        rows.append({
            "visit_id": int(v["visit_id"]),
            "data": s.strftime("%d/%m/%Y"),
            "início": s.strftime("%H:%M"),
            "fim": e.strftime("%H:%M"),
            "clínica": f"{v['clinic_id']} - {clinic_name}",
            "status": v["status"],
        })

    st.dataframe(rows, use_container_width=True)

    st.markdown("### Ação rápida")
    chosen = st.selectbox("Selecione a visita", options)
    v = visit_lookup[chosen]

    new_status = st.selectbox(
        "Atualizar status para",
        ["Agendado", "Realizado", "Reagendada", "Fechado Parceria", "Sem Parceria"],
        index=["Agendado", "Realizado", "Reagendada", "Fechado Parceria", "Sem Parceria"].index(v["status"])
    )

    if st.button("Atualizar status", type="primary"):
        visits_update(int(v["visit_id"]), {"status": new_status})
        apply_clinic_status_from_visit(int(v["clinic_id"]), new_status)
        st.success("Status atualizado!")
        st.rerun()

st.divider()
st.subheader("Tarefas vencidas")
if overdue:
    st.dataframe([
        {
            "task_id": t["task_id"],
            "clínica": (t.get("clinics") or {}).get("legal_name"),
            "título": t["title"],
            "vencimento": t["due_date"],
            "status": t["status"],
        }
        for t in overdue
    ], use_container_width=True)
else:
    st.success("Nenhuma tarefa vencida 🎉")
