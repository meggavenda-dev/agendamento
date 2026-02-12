import streamlit as st
from datetime import datetime, timezone
import pytz

def load_css(path: str = "assets/zen.css", focus_mode: bool = False):
    """Carrega CSS e ativa tema focus (alto contraste) se necessário."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        pass
    if focus_mode:
        # injeta classe no <body> para ativar o tema alternativo (alto contraste)
        st.markdown("<script>document.body.classList.add('theme-focus');</script>", unsafe_allow_html=True)

def priority_label(p: int) -> str:
    return {1: "Urgente", 2: "Importante", 3: "Normal", 4: "Baixa"}.get(int(p or 3), "Normal")

def priority_class(p: int) -> str:
    return {1: "badge-urgent", 2: "badge-warn", 3: "badge-accent", 4: "badge-ok"}.get(int(p or 3), "badge-accent")

def _parse_iso(iso: str):
    if not iso:
        return None
    try:
        dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return None

def fmt_dt(iso: str, tz_name: str = "America/Sao_Paulo") -> str:
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
    """Card visual consistente para itens (Agora/Semana)."""
    due_txt = fmt_dt(item.get("due_at") or item.get("start_at"), tz_name)
    rec = (item.get("recurrence") or "none").lower()
    rec_html = f"<span class='badge'>rec: {rec}</span>" if rec != "none" else ""
    pr_cls = priority_class(item.get("priority", 3))
    pr_lab = priority_label(item.get("priority", 3))
    notes = (item.get("notes") or "").strip()

    html = (
        "<div class='pa-card'>"
        + f"<div class='pa-card__title'>{item.get('title','')}</div>"
        + "<div class='pa-card__meta'>"
        + f"<span class='badge {pr_cls}'>{pr_lab}</span>"
        + f"<span class='badge badge-accent'>#{item.get('tag','geral')}</span>"
        + f"<span class='badge'>{item.get('status','todo')}</span>"
        + (f"<span class='badge'>Due: {due_txt}</span>" if due_txt else "")
        + rec_html
        + "</div>"
        + (f"<div class='pa-card__meta' style='margin-top:6px;'>{notes}</div>" if notes else "")
        + "</div>"
    )
    st.markdown(html, unsafe_allow_html=True)

def week_day_card(day_label: str, is_today: bool, inner_html: str) -> str:
    cls = "pa-day pa-day--today" if is_today else "pa-day"
    today_tag = "<span class='pa-day__today'>Hoje</span>" if is_today else ""
    return (
        f"<div class='{cls}'>"
        f"  <div class='pa-day__header'>"
        f"    <div class='pa-day__title'>{day_label}</div>"
        f"    {today_tag}"
        f"  </div>"
        f"  {inner_html}"
        f"</div>"
    )

def week_item_row(title: str, meta: str, priority: int) -> str:
    pcls = priority_class(priority); plab = priority_label(priority)
    return (
        "<div class='pa-card' style='padding:10px 12px;margin:8px 0;'>"
        f"  <div class='pa-card__title' style='font-size:0.98rem'>{title}</div>"
        f"  <div class='pa-card__meta'><span class='badge {pcls}'>{plab}</span> {meta}</div>"
        "</div>"
    )

def actions_row(buttons: list[tuple[str, str, str]]):
    """
    Renderiza uma linha de ações (classe pa-actions).
    buttons: lista de tuplas (label, variant, key)
      variant: 'primary' | 'ok' | 'danger' | '' (vazio = padrão)
    """
    st.markdown("<div class='pa-actions'>", unsafe_allow_html=True)
    cols = st.columns(len(buttons), gap="small")
    clicks = []
    for i, (label, variant, key) in enumerate(buttons):
        cls = "pa-btn" + (f" pa-btn--{variant}" if variant else "")
        with cols[i]:
            clicked = st.button(label, key=key, use_container_width=True)
            # aplica classe visual ao botão renderizado
            st.markdown(
                f"""
                <script>
                  const btns = [...document.querySelectorAll('button')];
                  const b = btns.find(x => x.innerText.trim() === "{label}");
                  if (b) b.className = "{cls}";
                </script>
                """,
                unsafe_allow_html=True
            )
        clicks.append(clicked)
    st.markdown("</div>", unsafe_allow_html=True)
    return clicks
