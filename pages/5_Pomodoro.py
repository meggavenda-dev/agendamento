
import streamlit as st
from datetime import datetime, timedelta, timezone
from core.auth import require_auth
from core.supa import supabase_user
from core.ui import load_css

st.set_page_config(page_title="Pomodoro", layout="wide")
load_css(); uid = require_auth(); sb = supabase_user()
st.title("Pomodoro")
items=(sb.table("items").select("id,title,estimated_minutes,spent_minutes").eq("user_id",uid).neq("status","done").order("priority").execute().data or [])
if not items: st.info("Sem itens pendentes."); st.stop()
choices={f"{it['title']} ({it['id'][:6]})":it['id'] for it in items}
choice=st.selectbox("Item", list(choices.keys()))
work=st.number_input("Foco (min)",10,120,25,5); brk=st.number_input("Pausa (min)",0,60,5,5)
if st.button("Iniciar"):
    st.session_state["pomodoro"]={"item_id":choices[choice],"start":datetime.now(timezone.utc).isoformat(),"work":int(work),"break":int(brk),"phase":"work"}
    st.experimental_rerun()
s=st.session_state.get("pomodoro")
if s:
    start=datetime.fromisoformat(s["start"]); dur=s["work"] if s["phase"]=="work" else s["break"]
    end=start+timedelta(minutes=dur); now=datetime.now(timezone.utc)
    rem=max(0,int((end-now).total_seconds())); st.write("Fase:", s["phase"], " Restante:", rem, "s")
    if rem==0:
        if s["phase"]=="work":
            try:
                it=sb.table("items").select("spent_minutes").eq("id",s["item_id"]).single().execute().data; spent=int(it.get("spent_minutes") or 0)
            except Exception: spent=0
            sb.table("items").update({"spent_minutes": spent + int(s["work"])}).eq("id",s["item_id"]).eq("user_id",uid).execute()
            s["phase"]="break" if s["break"]>0 else "done"; s["start"]=datetime.now(timezone.utc).isoformat(); st.session_state["pomodoro"]=s
        else:
            s["phase"]="done"; st.session_state["pomodoro"]=s
    if s["phase"]=="done":
        c1,c2=st.columns(2)
        if c1.button("Concluir item"):
            sb.table("items").update({"status":"done"}).eq("id",s["item_id"]).eq("user_id",uid).execute(); st.session_state.pop("pomodoro",None); st.success("Concluido")
        if c2.button("Nova sessao"):
            st.session_state.pop("pomodoro",None); st.experimental_rerun()
