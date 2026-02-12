
import streamlit as st
from datetime import datetime, timedelta, timezone
import pytz
from core.auth import require_auth
from core.supa import supabase_user
from core.queries import get_profile
from core.ui import load_css

st.set_page_config(page_title="Foco do Dia", layout="wide")
load_css(); uid = require_auth(); sb = supabase_user()
prof=get_profile(sb, uid); tz_name=prof.get("timezone","America/Sao_Paulo")
try: tz=pytz.timezone(tz_name)
except Exception: tz=pytz.timezone("America/Sao_Paulo")

st.title("Foco do Dia")
# exemplo simples: listar tarefas de hoje (top 3 por prioridade)
start = datetime.now(tz).replace(hour=0,minute=0,second=0,microsecond=0)
end = start + timedelta(days=1)
s_iso=start.astimezone(timezone.utc).isoformat(); e_iso=end.astimezone(timezone.utc).isoformat()
items=(sb.table("items").select("*").eq("user_id",uid).neq("status","done").gte("due_at",s_iso).lt("due_at",e_iso).order("priority").execute().data or [])
for it in items[:3]:
    st.write("- ", it.get("title",""))
