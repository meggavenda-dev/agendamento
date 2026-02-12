
import streamlit as st
import datetime
from core.auth import require_auth
from core.supa import supabase_user
from core.queries import fetch_agora, get_profile
from core.ui import load_css, item_card, actions_row

st.set_page_config(page_title="Agora • PulseAgenda", layout="wide")

uid = require_auth()
sb = supabase_user()
prof = get_profile(sb, uid) or {}
tz_name = prof.get("timezone","America/Sao_Paulo")
focus = (prof.get("theme") == "focus")
load_css(focus_mode=focus)

st.title("Agora")
st.caption("Atrasadas, próximas 24h e prioridades")

items = fetch_agora(sb, uid, tz_name)
if not items:
    st.info("Tudo em dia por aqui. Que tal planejar a semana?")
    st.stop()

def _parse_due(due_str: str):
    if not due_str: return None
    dt = datetime.datetime.fromisoformat(due_str.replace("Z","+00:00"))
    if dt.tzinfo is None: dt = dt.replace(tzinfo=datetime.timezone.utc)
    return dt

def _to_iso_utc(dt: datetime.datetime):
    if dt is None: return None
    if dt.tzinfo is None: dt = dt.replace(tzinfo=datetime.timezone.utc)
    return dt.astimezone(datetime.timezone.utc).replace(second=0,microsecond=0).isoformat()

for it in items:
    item_card(it, tz_name)
    c_done, c_delay, c_edit, c_del = actions_row([
        ("Concluir", "ok",     f"done_{it['id']}"),
        ("+1 dia",  "primary", f"delay_{it['id']}"),
        ("Editar",  "",        f"edit_{it['id']}") ,
        ("Excluir", "danger",  f"del_{it['id']}") ,
    ])
    if c_done:
        sb.table("items").update({"status":"done"}).eq("id", it["id"]).eq("user_id", uid).execute(); st.rerun()
    if c_delay:
        due = it.get("due_at")
        if due:
            dt_utc = _parse_due(due) + datetime.timedelta(days=1)
            sb.table("items").update({"due_at": _to_iso_utc(dt_utc)}).eq("id", it["id"]).eq("user_id", uid).execute(); st.rerun()
        else:
            st.warning("Sem prazo para adiar.")
    if c_edit:
        st.session_state[f"editing_{it['id']}"] = True
    if c_del:
        sb.table("items").delete().eq("id", it["id"]).eq("user_id", uid).execute(); st.rerun()
    if st.session_state.get(f"editing_{it['id']}"):
        st.markdown("<div class='pa-section'>", unsafe_allow_html=True)
        st.caption("Edição rápida")
        new_title = st.text_input("Título", value=it.get("title",""), key=f"title_{it['id']}")
        save = st.button("Salvar", key=f"save_{it['id']}")
        cancel = st.button("Cancelar", key=f"cancel_{it['id']}")
        if save:
            sb.table("items").update({"title": new_title.strip() or it.get("title","Item")}).eq("id", it["id"]).eq("user_id", uid).execute(); st.session_state.pop(f"editing_{it['id']}", None); st.success("Atualizado"); st.rerun()
        if cancel:
            st.session_state.pop(f"editing_{it['id']}", None); st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
