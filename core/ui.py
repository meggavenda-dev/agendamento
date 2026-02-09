import streamlit as st
from datetime import datetime, timezone
import pytz


def load_css(path: str = "assets/zen.css"):
    """
    Carrega CSS custom do app (tema Zen).
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        pass


def priority_label(p: int) -> str:
    return {1: "Urgente", 2: "Importante", 3: "Normal", 4: "Baixa"}.get(int(p or 3), "Normal")


def priority_class(p: int) -> str:
    return {1: "badge-urgent", 2: "badge-warn", 3: "badge-accent", 4: "badge-ok"}.get(int(p or 3), "badge-accent")


def _parse_iso(iso: str):
    """
    Converte ISO string (incluindo 'Z') em datetime com tzinfo.
    """
    if not iso:
        return None
    try:
        dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        # Se vier naive, assume UTC
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return None


def fmt_dt(iso: str, tz_name: str = "America/Sao_Paulo") -> str:
    """
    Formata datetime ISO exibindo no fuso local (tz_name).

    Recomendação:
    - banco salva em UTC (timestamptz)
    - UI converte para timezone do perfil
    """
    if not iso:
        return ""

    dt = _parse_iso(iso)
    if not dt:
        return str(iso)

    try:
        tz = pytz.timezone(tz_name) if tz_name else pytz.timezone("America/Sao_Paulo")
    except Exception:
        tz = pytz.timezone("America/Sao_Paulo")

    dt_local = dt.astimezone(tz)
    return dt_local.strftime("%d/%m %H:%M")


def item_card(item: dict, tz_name: str = "America/Sao_Paulo"):
    """
    Card do item.
    Exibe hora no fuso do usuário (tz_name).
    """
    # permite override por item (se você quiser setar item["tz_name"] nas queries)
    effective_tz = item.get("tz_name") or tz_name

    due_txt = fmt_dt(item.get("due_at") or item.get("start_at"), effective_tz)

    st.markdown(
        f"""
        <div class="pulse-card">
          <div class="pulse-title">{item.get('title','')}</div>
          <div class="pulse-meta">
            <span class="badge {priority_class(item.get('priority',3))}">{priority_label(item.get('priority',3))}</span>
            <span class="badge badge-accent">{item.get('tag','geral')}</span>
            <span class="badge">{item.get('status','todo')}</span>
            {f"<span class='badge'>⏰ {due_txt}</span>" if due_txt else ""}
          </div>
          <div class="pulse-meta" style="margin-top:6px;">{(item.get('notes') or '')}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def week_day_card(day_label: str, is_today: bool, inner_html: str) -> str:
    cls = "week-card-today" if is_today else "week-card"
    today_tag = "<span class='day-today'>Hoje</span>" if is_today else ""
    return (
        f"<div class='{cls}'>"
        f"  <div class='day-header'>"
        f"    <div class='day-title'>{day_label}</div>"
        f"    {today_tag}"
        f"  </div>"
        f"  {inner_html}"
        f"</div>"
    )


def week_item_row(title: str, meta: str, priority: int) -> str:
    pcls = priority_class(priority)
    plab = priority_label(priority)
    return (
        "<div class='item-row'>"
        f"  <div class='item-row-title'>{title}</div>"
        "  <div class='item-row-meta'>"
        f"    <span class='badge {pcls}'>{plab}</span> {meta}"
        "  </div>"
        "</div>"
    )
