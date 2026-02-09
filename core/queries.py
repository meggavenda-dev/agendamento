from datetime import datetime, timedelta, timezone
import pytz


def now_utc():
    return datetime.now(timezone.utc)


def get_profile(sb, user_id):
    """
    Retorna perfil do usuário.
    Se não existir, devolve defaults.
    """
    try:
        data = (
            sb.table("profiles")
            .select("timezone,theme,email_notifications,whatsapp_notifications,whatsapp_number,email,display_name")
            .eq("id", user_id)
            .single()
            .execute()
            .data
        )
        if isinstance(data, dict):
            # defaults mínimos
            data.setdefault("timezone", "America/Sao_Paulo")
            data.setdefault("theme", "zen")
            return data
        return {"timezone": "America/Sao_Paulo", "theme": "zen"}
    except Exception:
        return {"timezone": "America/Sao_Paulo", "theme": "zen"}


def week_range_for_tz(tz_name: str):
    """
    Semana = segunda 00:00 até próxima segunda 00:00 no fuso do usuário.
    Retorna (start_local, end_local, start_utc, end_utc, tz).
    """
    tz = pytz.timezone(tz_name or "America/Sao_Paulo")
    now_local = datetime.now(tz)

    # segunda-feira 00:00 local
    start_local = (now_local - timedelta(days=now_local.weekday())).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    end_local = start_local + timedelta(days=7)

    start_utc = start_local.astimezone(pytz.utc)
    end_utc = end_local.astimezone(pytz.utc)

    return start_local, end_local, start_utc, end_utc, tz


def fetch_agora(sb, user_id, tz_name: str = "America/Sao_Paulo"):
    """
    'Agora' = Atrasadas OR Próximas 24h OR Prioridade alta (1 ou 2).
    - Atrasadas: due_at < now
    - Próximas 24h: now <= due_at <= now+24h
    - Prioridade: priority <= 2 (mesmo sem due_at)
    Observação: status != done
    """
    n = now_utc().replace(second=0, microsecond=0)
    next24 = (n + timedelta(hours=24)).replace(second=0, microsecond=0)

    n_iso = n.isoformat()
    next_iso = next24.isoformat()

    # PostgREST OR clause:
    # - due_at.lt.now
    # - and(due_at.gte.now,due_at.lte.next24)
    # - priority.lte.2
    or_clause = (
        f"due_at.lt.{n_iso},"
        f"and(due_at.gte.{n_iso},due_at.lte.{next_iso}),"
        f"priority.lte.2"
    )

    try:
        res = (
            sb.table("items")
            .select("*")
            .eq("user_id", user_id)
            .neq("status", "done")
            .or_(or_clause)
            .order("priority", desc=False)
            .order("due_at", desc=False)
            .execute()
        )
        return res.data or []
    except Exception:
        return []


def fetch_semana(sb, user_id, tz_name: str = "America/Sao_Paulo"):
    """
    Itens com due_at dentro da semana local (segunda..domingo),
    convertendo intervalo para UTC para filtrar no banco.
    Mantém apenas status != done.
    """
    _, _, start_utc, end_utc, _ = week_range_for_tz(tz_name)

    start_iso = start_utc.replace(microsecond=0).isoformat()
    end_iso = end_utc.replace(microsecond=0).isoformat()

    try:
        res = (
            sb.table("items")
            .select("*")
            .eq("user_id", user_id)
            .neq("status", "done")
            .not_.is_("due_at", "null")
            .gte("due_at", start_iso)
            .lt("due_at", end_iso)
            .order("due_at", desc=False)
            .order("priority", desc=False)
            .execute()
        )
        return res.data or []
    except Exception:
        return []
