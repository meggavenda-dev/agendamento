from __future__ import annotations

from db import clinics


def apply_from_visit(clinic_id: int, visit_status: str) -> str | None:
    """Aplica regra progressiva de status (não regressiva por padrão).

    - Fechado Parceria => Ativo (sempre)
    - Sem Parceria => Perdido SOMENTE se ainda não estiver Ativo

    Retorna o novo status se houver mudança; caso contrário, None.
    """
    c = clinics.get_by_id(clinic_id)
    current = (c or {}).get("status") or "Prospect"

    if visit_status == "Fechado Parceria":
        if current != "Ativo":
            clinics.update(clinic_id, {"status": "Ativo"})
            return "Ativo"
        return None

    if visit_status == "Sem Parceria":
        if current not in ("Ativo", "Perdido"):
            clinics.update(clinic_id, {"status": "Perdido"})
            return "Perdido"
        return None

    return None
