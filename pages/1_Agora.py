import streamlit as st
import datetime

from core.auth import require_auth
from core.supa import supabase_user
from core.queries import fetch_agora, get_profile
from core.ui import load_css, item_card

st.set_page_config(page_title="Agora • PulseAgenda", layout="wide")
load_css()

uid = require_auth()

# ✅ use o client logado (JWT) — necessário para RLS e para update/delete
sb = supabase_user()

profile = get_profile(sb, uid)
tz_name = profile.get("timezone", "America/Sao_Paulo")

st.title("⚡ Agora")
st.caption("Atrasadas • Próximas 24h • Prioridades")

items = fetch_agora(sb, uid, tz_name)

if not items:
    st.info("Tudo em dia por aqui. Que tal planejar a semana? 🙂")
    st.stop()

def _parse_due(due_str: str):
    if not due_str:
        return None
    # suporta "Z"
    return datetime.datetime.fromisoformat(due_str.replace("Z", "+00:00"))

def _to_iso(dt: datetime.datetime):
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=datetime.timezone.utc)
    return dt.astimezone(datetime.timezone.utc).isoformat()

for it in items:
    item_card(it)

    # ações rápidas
    c1, c2, c3, c4 = st.columns([1, 1, 1, 1])

    with c1:
        if st.button("✅ Concluir", key=f"done_{it['id']}", use_container_width=True):
            sb.table("items").update({"status": "done"}).eq("id", it["id"]).eq("user_id", uid).execute()
            st.rerun()

    with c2:
        if st.button("⏳ Adiar 1 dia", key=f"delay_{it['id']}", use_container_width=True):
            due = it.get("due_at")
            if due:
                dt = _parse_due(due)
                dt = dt + datetime.timedelta(days=1)
                sb.table("items").update({"due_at": _to_iso(dt)}).eq("id", it["id"]).eq("user_id", uid).execute()
                st.rerun()
            else:
                st.warning("Esse item não tem prazo/horário para adiar.")

    with c3:
        if st.button("✏️ Editar", key=f"edit_{it['id']}", use_container_width=True):
            st.session_state[f"editing_{it['id']}"] = True

    with c4:
        if st.button("🗑️ Excluir", key=f"del_{it['id']}", use_container_width=True):
            st.session_state[f"confirm_del_{it['id']}"] = True

    # -----------------------
    # EDIÇÃO INLINE (sem modal)
    # -----------------------
    if st.session_state.get(f"editing_{it['id']}", False):
        st.divider()
        st.caption("Edição rápida")

        ec1, ec2 = st.columns([3, 2])
        new_title = ec1.text_input("Título", value=it.get("title", ""), key=f"title_{it['id']}")
        new_tag = ec2.text_input("Tag", value=it.get("tag", "geral"), key=f"tag_{it['id']}")

        ec3, ec4 = st.columns([2, 2])
        # prioridade 1..4 (igual seu Criar)
        new_priority = ec3.select_slider(
            "Prioridade",
            options=[1, 2, 3, 4],
            value=int(it.get("priority", 2)),
            format_func=lambda x: {1: "Urgente", 2: "Importante", 3: "Normal", 4: "Baixa"}[x],
            key=f"prio_{it['id']}",
        )

        # due_at pode ser None
        due_dt = _parse_due(it.get("due_at")) if it.get("due_at") else None
        if due_dt:
            due_default = due_dt.astimezone(datetime.timezone.utc)
        else:
            due_default = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=2)

        new_due = ec4.datetime_input("Prazo / Horário", value=due_default, key=f"due_{it['id']}")

        new_notes = st.text_area("Notas", value=it.get("notes") or "", key=f"notes_{it['id']}")

        b1, b2 = st.columns([1, 1])
        if b1.button("💾 Salvar alterações", key=f"save_{it['id']}", use_container_width=True):
            if not new_title.strip():
                st.error("Título não pode ficar vazio.")
            else:
                payload = {
                    "title": new_title.strip(),
                    "tag": (new_tag.strip() or "geral"),
                    "priority": int(new_priority),
                    "due_at": _to_iso(new_due),
                    "notes": (new_notes.strip() if new_notes.strip() else None),
                }
                sb.table("items").update(payload).eq("id", it["id"]).eq("user_id", uid).execute()
                st.session_state.pop(f"editing_{it['id']}", None)
                st.success("Item atualizado ✅")
                st.rerun()

        if b2.button("Cancelar", key=f"cancel_{it['id']}", use_container_width=True):
            st.session_state.pop(f"editing_{it['id']}", None)
            st.rerun()

    # -----------------------
    # EXCLUSÃO COM CONFIRMAÇÃO
    # -----------------------
    if st.session_state.get(f"confirm_del_{it['id']}", False):
        st.warning("Tem certeza que deseja excluir este item? Essa ação não pode ser desfeita.")
        d1, d2 = st.columns([1, 1])

        if d1.button("✅ Sim, excluir", key=f"yes_del_{it['id']}", use_container_width=True):
            # se reminders tiver FK com cascade, isso é opcional.
            # aqui removemos reminders por segurança:
            try:
                sb.table("reminders").delete().eq("item_id", it["id"]).eq("user_id", uid).execute()
            except Exception:
                pass

            sb.table("items").delete().eq("id", it["id"]).eq("user_id", uid).execute()
            st.session_state.pop(f"confirm_del_{it['id']}", None)
            st.success("Item excluído 🗑️")
            st.rerun()

        if d2.button("Não", key=f"no_del_{it['id']}", use_container_width=True):
            st.session_state.pop(f"confirm_del_{it['id']}", None)
            st.rerun()
