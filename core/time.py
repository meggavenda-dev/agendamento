from __future__ import annotations

from datetime import datetime, date, time
from dateutil import tz


def get_tz_name() -> str:
    """Timezone padrão do app."""
    # Import local para evitar dependência circular com Streamlit em módulos puros
    try:
        import streamlit as st
        return st.secrets.get("TIMEZONE", "America/Sao_Paulo")
    except Exception:
        return "America/Sao_Paulo"


def get_zone(tz_name: str | None = None):
    return tz.gettz(tz_name or get_tz_name())


def to_utc_iso(dt: datetime) -> str:
    """Converte datetime timezone-aware para ISO em UTC."""
    return dt.astimezone(tz.UTC).isoformat()


def from_utc_iso(iso_str: str, tz_name: str | None = None) -> datetime:
    """Converte string ISO (com Z ou offset) para datetime no timezone local."""
    zone = get_zone(tz_name)
    s = iso_str.replace("Z", "+00:00")
    return datetime.fromisoformat(s).astimezone(zone)


def local_day_bounds_utc(d: date, tz_name: str | None = None) -> tuple[str, str]:
    """Retorna (start_utc_iso, end_utc_iso) cobrindo o dia local inteiro."""
    zone = get_zone(tz_name)
    start_local = datetime.combine(d, time(0, 0, 0)).replace(tzinfo=zone)
    end_local = datetime.combine(d, time(23, 59, 59)).replace(tzinfo=zone)
    return to_utc_iso(start_local), to_utc_iso(end_local)
