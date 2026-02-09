import streamlit as st
from datetime import datetime, timedelta, timezone

from core.auth import require_auth
from core.supa import supabase_anon
from core.ui import load_css

st.set_page_config(page_title="Criar • PulseAgenda", layout="wide")
load_css()

uid = require_auth()
sb = supabase_anon()

st.title("➕ Criar")

with st.form("create_item"):
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

    due = st.datetime_input("Prazo / Horário", value=datetime.now(timezone.utc) + timedelta(hours=2))
    estimated = st.number_input("Tempo estimado (min)", min_value=5, max_value=480, value=30, step=5)

    st.markdown("#### Lembretes")
    remind_in_app = st.checkbox("In-app", value=True)
    remind_email = st.checkbox("E-mail", value=True)
    remind_whats = st.checkbox("WhatsApp", value=False)
    remind_before = st.selectbox("Avisar antes", [0, 5, 10, 15, 30, 60], index=3)

    submit = st.form_submit_button("Salvar", use_container_width=True)

if submit:
    if not title.strip():
        st.error("Título é obrigatório.")
        st.stop()

    item = {
        "user_id": uid,
        "type": itype,
        "title": title.strip(),
        "notes": notes.strip() if notes else None,
        "tag": tag.strip() if tag else "geral",
        "priority": int(priority),
        "status": "todo",
        "due_at": due.isoformat(),
        "estimated_minutes": int(estimated),
    }

    ins = sb.table("items").insert(item).execute()
    item_id = ins.data[0]["id"]

    remind_at = due - timedelta(minutes=int(remind_before))

    def add_rem(channel: str):
        sb.table("reminders").insert({
            "user_id": uid,
            "item_id": item_id,
            "remind_at": remind_at.isoformat(),
            "channel": channel,
        }).execute()

    if remind_in_app:
        add_rem("in_app")
    if remind_email:
        add_rem("email")
    if remind_whats:
        add_rem("whatsapp")

    st.success("Criado ✅")
