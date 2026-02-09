import streamlit as st
from datetime import datetime, timedelta, timezone
import pytz

from core.auth import require_auth
from core.supa import supabase_user
from core.queries import get_profile
from core.ui import load_css

st.set_page_config(page_title="Criar • PulseAgenda", layout="wide")
load_css()

uid = require_auth()
sb = supabase_user()

# ====== Toast/sucesso persistente após rerun ======
if st.session_state.pop("created_success", False):
    st.success("Criado ✅")

# ====== timezone do perfil ======
profile = get_profile(sb, uid) or {}
tz_name = profile.get("timezone", "America/Sao_Paulo")

try:
    tz = pytz.timezone(tz_name)
except Exception:
    tz = pytz.timezone("America/Sao_Paulo")
    tz_name = "America/Sao_Paulo"

st.title("➕ Criar")
st.caption(f"Fuso horário do app: **{tz_name}**")

# default: agora + 2h no fuso local, com segundos zerados
default_local = datetime.now(tz).replace(second=0, microsecond=0) + timedelta(hours=2)

with st.form("create_item", clear_on_submit=False):
    itype = st.selectbox(
        "Tipo",
        ["task", "meeting", "event"],
        format_func=lambda x: {"task": "Tarefa", "meeting": "Reunião", "event": "Evento"}[x],
    )

    title = st.text_input("Título*", placeholder="Ex: Reunião com equipe / Enviar relatório / Academia")
    notes = st.text_area("Notas", placeholder="Detalhes rápidos (opcional)")

    c1, c2 = st.columns(2)
    with c1:
        tag = st.text_input("Tag", value="trabalho")
    with c2:
        priority = st.select_slider(
            "Prioridade",
            options=[1, 2, 3, 4],
            value=2,
            format_func=lambda x: {1: "Urgente", 2: "Importante", 3: "Normal", 4: "Baixa"}[x],
        )

    # usuário escolhe no fuso local
    due_local = st.datetime_input("Prazo / Horário", value=default_local)

    # normaliza segundos sempre (evita 22:53:12 etc.)
    if isinstance(due_local, datetime):
        due_local = due_local.replace(second=0, microsecond=0)

    estimated = st.number_input("Tempo estimado (min)", min_value=5, max_value=480, value=30, step=5)

    st.markdown("#### Lembretes")
    remind_in_app = st.checkbox("In-app", value=True)
    remind_email = st.checkbox("E-mail", value=True)
    remind_whats = st.checkbox("WhatsApp", value=False)
    remind_before = st.selectbox("Avisar antes", [0, 5, 10, 15, 30, 60], index=3)

    # Preview para evitar confusão de UTC x local
    # Streamlit pode devolver datetime "naive" (sem tzinfo) — trate como local do perfil
    due_local_for_preview = due_local
    if due_local_for_preview.tzinfo is None:
        due_local_for_preview = tz.localize(due_local_for_preview)

    due_utc_preview = due_local_for_preview.astimezone(timezone.utc)
    st.caption(
        f"🕒 Você escolheu **{due_local_for_preview.strftime('%d/%m/%Y %H:%M')}** (local) "
        f"→ será salvo como **{due_utc_preview.strftime('%Y-%m-%d %H:%MZ')}** (UTC)."
    )

    submit = st.form_submit_button("Salvar", use_container_width=True)

if submit:
    if not title.strip():
        st.error("Título é obrigatório.")
        st.stop()

    # garante aware datetime no fuso do perfil
    if due_local.tzinfo is None:
        due_local = tz.localize(due_local)

    # converte para UTC para salvar no banco
    due_utc = due_local.astimezone(timezone.utc)

    item = {
        "user_id": uid,
        "type": itype,
        "title": title.strip(),
        "notes": notes.strip() if notes else None,
        "tag": tag.strip() if tag else "geral",
        "priority": int(priority),
        "status": "todo",
        "due_at": due_utc.isoformat(),  # UTC no banco
        "estimated_minutes": int(estimated),
    }

    try:
        ins = sb.table("items").insert(item).execute()
        item_id = ins.data[0]["id"]
    except Exception as e:
        st.error(f"Erro ao criar item: {e}")
        st.stop()

    remind_at_utc = due_utc - timedelta(minutes=int(remind_before))

    def add_rem(channel: str):
        sb.table("reminders").insert({
            "user_id": uid,
            "item_id": item_id,
            "remind_at": remind_at_utc.isoformat(),
            "channel": channel,
        }).execute()

    try:
        if remind_in_app:
            add_rem("in_app")
        if remind_email:
            add_rem("email")
        if remind_whats:
            add_rem("whatsapp")

        # ✅ sucesso persistente após rerun
        st.session_state["created_success"] = True
        st.rerun()

    except Exception as e:
        # item criado, lembretes falharam
        st.warning("Item criado, mas ocorreu erro ao salvar lembretes.")
        st.error(str(e))
