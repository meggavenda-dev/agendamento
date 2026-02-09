from __future__ import annotations

from datetime import datetime

from core.time import to_utc_iso
from core.scheduler import assert_no_conflict
from db import visits as visits_db
from db import clinics as clinics_db


def create_visit(
    clinic_id: int,
    start_local: datetime,
    end_local: datetime,
    existing_local: list[dict],
):
    """Cria visita com validação de conflito + automação (primeira visita)."""
    assert_no_conflict(start_local, end_local, existing_local)

    c = clinics_db.get_by_id(clinic_id)
    if not c:
        raise ValueError("Clínica não encontrada. Cadastre/importe primeiro.")

    had_any = visits_db.clinic_has_any_visit(clinic_id)
    clinic_status = (c.get("status") or "Prospect")

    visits_db.create(
        {
            "clinic_id": int(clinic_id),
            "start_at": to_utc_iso(start_local),
            "end_at": to_utc_iso(end_local),
            "status": "Agendado",
        }
    )

    # Automação: primeira visita e clínica Prospect => Em negociação
    if (not had_any) and clinic_status == "Prospect":
        clinics_db.update(clinic_id, {"status": "Em negociação"})


def reschedule_visit(
    visit_id: int,
    new_start_local: datetime,
    new_end_local: datetime,
    others_local: list[dict],
):
    assert_no_conflict(new_start_local, new_end_local, others_local)
    visits_db.update(
        int(visit_id),
        {
            "start_at": to_utc_iso(new_start_local),
            "end_at": to_utc_iso(new_end_local),
            "status": "Reagendada",
        },
    )
