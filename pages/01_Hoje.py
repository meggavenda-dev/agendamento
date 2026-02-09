import streamlit as st
from datetime import datetime, timedelta
from dateutil import tz

from db.visits import list_range
from db.tasks import list_overdue
from services.visits_service import update_visit_and_maybe_clinic

st.header("📍 Hoje")

tz_name = st.secrets.get("TIMEZONE", "America/Sao_Paulo")
zone = tz.gettz(tz_name)
now = datetime.now(zone)

start_today = now.replace(hour=0, minute=0, second=0, microsecond=0)
end_plus3 = (start_today + timedelta(days=3)).replace(hour=23, minute=59, second=59, microsecond=0)

visits = list_range(
    start_today.astimezone(tz.UTC).isoformat(),
    end_plus3.astimezone(tz.UTC).isoformat(),
)

today_iso = now.date().isoformat()
overdue = list_overdue(today_iso)

st.subheader("Visitas (Hoje + próximos 3 dias)")
if not visits:
    st.info("Sem visitas no período.")
else:
    rows = []
    options = []
    lookup = {}

    for v in visits:
        s = datetime.fromisoformat(v["start_at"].replace("Z", "+00:00")).astimezone(zone)
        e = datetime.fromisoformat(v["end_at"].replace("Z", "+00:00")).astimezone(zone)
        clinic_name = (v.get("clinics") or {}).get("legal_name")

        opt = f"#{v['visit_id']} | {s.strftime('%d/%m %H:%M')} | {v['clinic_id']} - {clinic_name} | {v['status']}"
        options.append(opt)
        lookup[opt] = v

        rows.append(
            {
                "visit_id": int(v["visit_id"]),
                "data": s.strftime("%d/%m/%Y"),
                "início": s.strftime("%H:%M"),
                "fim": e.strftime("%H:%M"),
                "clínica": f"{v['clinic_id']} - {clinic_name}",
                "status": v["status"],
            }
        )

    st.dataframe(rows, use_container_width=True)

    st.markdown("### Ação rápida")
    chosen = st.selectbox("Selecione a visita", options)
    v = lookup[chosen]

    status_options = ["Agendado", "Realizado", "Reagendada", "Fechado Parceria", "Sem Parceria"]
    new_status = st.selectbox(
        "Atualizar status para",
        status_options,
        index=status_options.index(v["status"]) if v.get("status") in status_options else 0,
    )

    if st.button("Atualizar status", type="primary"):
        update_visit_and_maybe_clinic(int(v["visit_id"]), int(v["clinic_id"]), {"status": new_status})
        st.success("Status atualizado!")
        st.rerun()

st.divider()

st.subheader("Tarefas vencidas")
if overdue:
    st.dataframe(
        [
            {
                "task_id": t["task_id"],
                "clínica": (t.get("clinics") or {}).get("legal_name"),
                "título": t["title"],
                "vencimento": t["due_date"],
                "status": t["status"],
            }
            for t in overdue
        ],
        use_container_width=True,
    )
else:
    st.success("Nenhuma tarefa vencida 🎉")
