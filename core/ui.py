import streamlit as st
from datetime import datetime


def load_css(path: str = "assets/zen.css"):
    try:
        with open(path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        pass


def priority_label(p: int) -> str:
    return {1: "Urgente", 2: "Importante", 3: "Normal", 4: "Baixa"}.get(p, "Normal")


def priority_class(p: int) -> str:
    return {1: "badge-urgent", 2: "badge-warn", 3: "badge-accent", 4: "badge-ok"}.get(p, "badge-accent")


def fmt_dt(iso: str) -> str:
    if not iso:
        return ""
    try:
        dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        return dt.strftime("%d/%m %H:%M")
    except Exception:
        return str(iso)


def item_card(item: dict):
    due_txt = fmt_dt(item.get("due_at") or item.get("start_at"))
    st.markdown(
        f"""
        <div class="pulse-card">
          <div class="pulse-title">{item['title']}</div>
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
