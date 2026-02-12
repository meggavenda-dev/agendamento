
import streamlit as st
import datetime, pytz
from core.auth import require_auth
from core.supa import supabase_user
from core.queries import fetch_agora, get_profile
from core.ui import load_css

st.set_page_config(page_title="Agora", layout="wide")
load_css()
uid = require_auth(); sb = supabase_user()
prof = get_profile(sb, uid); tz_name = prof.get("timezone","America/Sao_Paulo")
items = fetch_agora(sb, uid, tz_name)

st.title("Agora")
if not items:
    st.info("Sem itens. Crie algo em 'Criar'."); st.stop()

for it in items:
    with st.container(border=True):
        st.write(it.get("title","(sem titulo)"))
        cols = st.columns(4)
        if cols[0].button("Concluir", key=f"done_{it['id']}"):
            sb.table("items").update({"status":"done"}).eq("id", it["id"]).eq("user_id", uid).execute(); st.rerun()
        if cols[1].button("+1d", key=f"delay_{it['id']}"):
            due = it.get("due_at");
            if due:
                dt = datetime.datetime.fromisoformat(due.replace("Z","+00:00"))
                if dt.tzinfo is None: dt = dt.replace(tzinfo=datetime.timezone.utc)
                dt = dt + datetime.timedelta(days=1)
                sb.table("items").update({"due_at": dt.astimezone(datetime.timezone.utc).replace(second=0,microsecond=0).isoformat()}).eq("id", it["id"]).eq("user_id", uid).execute(); st.rerun()
        if cols[2].button("Editar", key=f"edit_{it['id']}"):
            st.session_state[f"editing_{it['id']}"] = True
        if cols[3].button("Excluir", key=f"del_{it['id']}"):
            sb.table("items").delete().eq("id", it["id"]).eq("user_id", uid).execute(); st.rerun()

        if st.session_state.get(f"editing_{it['id']}"):
            new_title = st.text_input("Titulo", value=it.get("title",""), key=f"title_{it['id']}")
            if st.button("Salvar", key=f"save_{it['id']}"):
                sb.table("items").update({"title": new_title.strip() or it.get("title","Item")}).eq("id", it["id"]).eq("user_id", uid).execute();
                st.session_state.pop(f"editing_{it['id']}", None); st.rerun()
