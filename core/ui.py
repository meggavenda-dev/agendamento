# core/ui.py
import os
import streamlit as st

# Caminho para o CSS do tema
_ASSETS_CSS = os.path.join("assets", "zen.css")

def load_css(focus_mode: bool = False):
    """
    Carrega o CSS de tema e aplica classe opcional 'theme-focus' no <body>.
    """
    css = ""
    try:
        with open(_ASSETS_CSS, "r", encoding="utf-8") as f:
            css = f.read()
    except Exception:
        # fallback simples caso o arquivo não exista
        css = ":root{--bg:#fff;--text:#111} body{background:var(--bg);color:var(--text)}"

    body_class = "theme-focus" if focus_mode else ""
    st.markdown(
        f"<style>{css}</style><body class='{body_class}'></body>",
        unsafe_allow_html=True
    )

def priority_label(p: int) -> str:
    """
    Converte prioridade numérica em rótulo.
    """
    p = int(p or 3)
    return {1: "Alta", 2: "Média", 3: "Normal", 4: "Baixa"}.get(p, "Normal")

# ---------- Componentes usados na página "Agora" ----------
def item_card(item: dict, tz_name: str) -> None:
    """
    Renderiza um cartão simples de item (título, tag, prioridade).
    """
    title = item.get("title", "Item")
    tag = item.get("tag", "geral")
    pr = priority_label(item.get("priority", 3))
    st.markdown(
        f"""
        <div class="pa-card">
            <div class="pa-card__title">{title}</div>
            <div class="pa-card__meta">#{tag} • {pr}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

def actions_row(actions: list[tuple[str, str, str]]):
    """
    Linha de botões de ação.
    actions: lista [(label, variant, key), ...]
    Retorna uma tupla de bools na mesma ordem (se foi clicado).
    """
    cols = st.columns(len(actions))
    out = []
    for i, (label, variant, key) in enumerate(actions):
        kwargs = {}
        # você pode mapear estilos por variant, se quiser
        if variant == "danger":
            kwargs["type"] = "secondary"
        elif variant in ("primary", "ok"):
            kwargs["type"] = "primary"
        out.append(cols[i].button(label, key=key, use_container_width=True, **kwargs))
    return tuple(out)

# ---------- Componentes usados na página "Semana" ----------
def week_item_row(title: str, meta: str, priority: int) -> str:
    pr = priority_label(priority)
    return (
        f"<div class='pa-card'>"
        f"  <div class='pa-card__title'>{title}</div>"
        f"  <div class='pa-card__meta'>{meta} • {pr}</div>"
        f"</div>"
    )

def week_day_card(label: str, is_today: bool, inner_html: str) -> str:
    today_cls = " pa-day--today" if is_today else ""
    return (
        f"<div class='pa-day{today_cls}'>"
        f"  <div class='pa-day__header'>"
        f"    <div class='pa-day__title'>{label}</div>"
        f"    {'<div class=\"pa-day__today\">HOJE</div>' if is_today else ''}"
        f"  </div>"
        f"{inner_html}"
        f"</div>"
    )
