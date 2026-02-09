from __future__ import annotations

from db import visits
from services.clinic_status import apply_from_visit


def update_visit_and_maybe_clinic(visit_id: int, clinic_id: int, payload: dict):
    """Atualiza visita e aplica regra de status progressivo da clínica, se necessário."""
    visits.update(visit_id, payload)
    new_status = payload.get("status")
    if new_status:
        apply_from_visit(clinic_id, new_status)
