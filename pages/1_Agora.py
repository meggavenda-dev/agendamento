import streamlit as st
import datetime
import pytz

from core.auth import require_auth
from core.supa import supabase_user
from core.queries import fetch_agora, get_profile
from core.ui import load_css, item_card

st.set_page_config(page_title="Agora • PulseAgenda", layout="wide")
load_css()

uid = require_auth()

# ✅ client logado (RLS + updates/deletes)
sb = supabase_user()

profile = get_profile(sb, uid) or {}
tz_name = profile.get("timezone", "America/Sao_Paulo")

st.title("⚡ Agora")
st.caption("Atrasadas • Próximas 24h • Prioridades")

items = fetch_agora(sb, uid, tz_name)

if not items:
    st.info("Tudo em dia por aqui. Que tal planejar a semana? 🙂")
    st.stop()

# timezone helper
try:
    tz = pytz.timezone(tz_name)
except Exception:
    tz = pytz.timezone("America/Sao_Paulo")
    tz_name = "America/Sao_Paulo"


def _parse_due(due_str: str):
    if not due_str:
        return None
    dt = datetime.datetime.fromisoformat(due_str.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=datetime.timezone.utc)
    return dt


def _to_iso_utc(dt: datetime.datetime):
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=datetime.timezone.utc)
    return dt.astimezone(datetime.timezone.utc).replace(second=0, microsecond=0).isoformat()


for it in items:
    # ✅ exibe no fuso do perfil (se você aplicou o ui.py atualizado)
    item_card(it, tz_name)

    # ===== Linha de botões compactos (mobile) =====
    st.markdown("<div class='action-row'>", unsafe_allow_html=True)
    b1, b2, b3, b4 = st.columns([1, 1, 1, 1], gap="small")

    with b1:
        if st.button("✅ Concluir", key=f"done_{it['id']}", use_container_width=True):
            sb.table("items").update({"status": "done"}).eq("id", it["id"]).eq("user_id", uid).execute()
            st.rerun()

    with b2:
        if st.button("⏳ +1d", key=f"delay_{it['id']}", use_container_width=True):
            due = it.get("due_at")
            if due:
                dt_utc = _parse_due(due)
                dt_utc = dt_utc + datetime.timedelta(days=1)
                sb.table("items").update({"due_at": _to_iso_utc(dt_utc)}).eq("id", it["id"]).eq("user_id", uid).execute()
                st.rerun()
            else:
                st.warning("Esse item não tem prazo/horário para adiar.")

    with b3:
        if st.button("✏️ Editar", key=f"edit_{it['id']}", use_container_width=True):
            st.session_state[f"editing_{it['id']}"] = True

    with b4:
        if st.button("🗑️ Excluir", key=f"del_{it['id']}", use_container_width=True):
            st.session_state[f"confirm_del_{it['id']}"] = True

    st.markdown("</div>", unsafe_allow_html=True)

    # ===== EDIÇÃO INLINE =====
    if st.session_state.get(f"editing_{it['id']}", False):
        st.divider()
        st.caption("Edição rápida")

        ec1, ec2 = st.columns([3, 2])
        new_title = ec1.text_input("Título", value=it.get("title", ""), key=f"title_{it['id']}")
        new_tag = ec2.text_input("Tag", value=it.get("tag", "geral"), key=f"tag_{it['id']}")

        ec3, ec4 = st.columns([2, 2])
        new_priority = ec3.select_slider(
            "Prioridade",
            options=[1, 2, 3, 4],
            value=int(it.get("priority", 2)),
            format_func=lambda x: {1: "Urgente", 2: "Importante", 3: "Normal", 4: "Baixa"}[x],
            key=f"prio_{it['id']}",
        )

        # mostra o datetime_input em LOCAL (fica natural no celular)
        due_dt = _parse_due(it.get("due_at")) if it.get("due_at") else None
        if due_dt:
            due_local = due_dt.astimezone(tz).replace(second=0, microsecond=0)
        else:
            due_local = (datetime.datetime.now(tz) + datetime.timedelta(hours=2)).replace(second=0, microsecond=0)

        new_due_local = ec4.datetime_input("Prazo / Horário", value=due_local, key=f"due_{it['id']}")

        # Streamlit às vezes devolve naive; interpretamos como local
        if new_due_local.tzinfo is None:
            new_due_local = tz.localize(new_due_local)
        new_due_utc = new_due_local.astimezone(datetime.timezone.utc).replace(second=0, microsecond=0)

        new_notes = st.text_area("Notas", value=it.get("notes") or "", key=f"notes_{it['id']}")

        c_save, c_cancel = st.columns([1, 1])
        if c_save.button("💾 Salvar", key=f"save_{it['id']}", use_container_width=True):
            if not new_title.strip():
                st.error("Título não pode ficar vazio.")
            else:
                payload = {
                    "title": new_title.strip(),
                    "tag": (new_tag.strip() or "geral"),
                    "priority": int(new_priority),
                    "due_at": new_due_utc.isoformat(),
                    "notes": (new_notes.strip() if new_notes.strip() else None),
                }
                sb.table("items").update(payload).eq("id", it["id"]).eq("user_id", uid).execute()
                st.session_state.pop(f"editing_{it['id']}", None)
                st.success("Item atualizado ✅")
                st.rerun()

        if c_cancel.button("Cancelar", key=f"cancel_{it['id']}", use_container_width=True):
            st.session_state.pop(f"editing_{it['id']}", None)
            st.rerun()

    # ===== EXCLUSÃO COM CONFIRMAÇÃO =====
    if st.session_state.get(f"confirm_del_{it['id']}", False):
        st.warning("Tem certeza que deseja excluir este item? Essa ação não pode ser desfeita.")
        d1, d2 = st.columns([1, 1])

        if d1.button("✅ Sim", key=f"yes_del_{it['id']}", use_container_width=True):
            # remove lembretes relacionados (se existir)
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
