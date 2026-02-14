# pages/6_Entrada_Rapida.py
import os
import sys
import re
import streamlit as st
from datetime import datetime, timedelta, timezone
import pytz

APP_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if APP_ROOT not in sys.path:
    sys.path.insert(0, APP_ROOT)

from core.auth import require_auth
from core.supa import supabase_user
from core.queries import get_profile
from core.ui import load_css

st.set_page_config(page_title="Entrada Rápida • PulseAgenda", layout="wide")

sb = supabase_user()
uid = require_auth()

prof = get_profile(sb, uid) or {}
tz_name = prof.get("timezone", "America/Sao_Paulo")
focus = (prof.get("theme") == "focus")
load_css(focus_mode=focus)

tz = pytz.timezone(tz_name)

st.title("Entrada Rápida")
st.caption("Ex.: 'Reunião amanhã 15h #trabalho !1 (30min) semanal qua,sex'")

text = st.text_input("Comando", "Enviar relatório sexta 14:30 #trabalho !2 (45min) semanal qua,sex")

def parse(t: str):
    o = {
        "title": t,
        "tag": None,
        "priority": 3,
        "estimated": 30,
        "due_local": None,
        "type": "task",
        "recurrence": "none",
        "recur_interval": 1,
        "recur_weekdays": None
    }

    m = re.findall(r"#(\w+)", t)
    if m:
        o["tag"] = m[0]
        t = re.sub(r"#\w+", "", t)

    m = re.findall(r"!(\d)", t)
    if m:
        o["priority"] = max(1, min(4, int(m[0])))
        t = re.sub(r"!\d", "", t)

    m = re.findall(r"\((\d{1,3})\s*min\)", t)
    if m:
        o["estimated"] = int(m[0])
        t = re.sub(r"\(\d{1,3}\s*min\)", "", t)

    base = datetime.now(tz).replace(second=0, microsecond=0)
    due = None
    if re.search(r"amanhã", t, re.I) or re.search(r"amanha", t, re.I):
        due = base + timedelta(days=1)
    elif re.search(r"hoje", t, re.I):
        due = base

    dias = {"seg": 0, "ter": 1, "qua": 2, "qui": 3, "sex": 4, "sab": 5, "dom": 6}
    for k, v in dias.items():
        if re.search(rf"{k}", t, re.I):
            delta = (v - base.weekday()) % 7
            due = base + timedelta(days=delta)
            break

    m = re.findall(r"(\d{1,2})/(\d{1,2})", t)
    if m:
        d, mo = map(int, m[0])
        due = (due or base).replace(year=base.year, month=mo, day=d)
        t = re.sub(r"\d{1,2}/\d{1,2}", "", t)

    m = re.findall(r"(\d{1,2})(?::|h)?(\d{2})?h?", t)
    if m:
        hh = int(m[0][0])
        mm = int(m[0][1] or 0)
        due = (due or base).replace(hour=hh, minute=mm)

    if not due:
        due = base + timedelta(hours=2)
    o["due_local"] = due

    low = t.lower()
    if "todo dia" in low or "todos os dias" in low:
        o["recurrence"] = "daily"
    elif "semanal" in low or "toda semana" in low:
        o["recurrence"] = "weekly"
        m = re.findall(r"semanal\s+([a-z,]+)", low)
        if m:
            mapa = {"seg":"mon","ter":"tue","qua":"wed","qui":"thu","sex":"fri","sab":"sat","dom":"sun"}
            dias_list = [mapa.get(x.strip()[:3], "") for x in m[0].split(',')]
            dias_list = [x for x in dias_list if x]
            o["recur_weekdays"] = ','.join(dias_list) or None
    elif re.search(r"a\s*cada\s*(\d+)\s*dias", low):
        o["recurrence"] = "every_x_days"
        o["recur_interval"] = int(re.findall(r"a\s*cada\s*(\d+)\s*dias", low)[0])
    elif "seg a sex" in low or "segunda a sexta" in low:
        o["recurrence"] = "workdays"

    return o, t.strip()

if text:
    parsed, cleaned = parse(text)
    st.write("Preview:", cleaned or text)

    if st.button("Criar", use_container_width=True):
        due_utc = parsed["due_local"].astimezone(timezone.utc)
        item = {
            "user_id": uid,
            "type": parsed["type"],
            "title": cleaned or text,
            "tag": parsed["tag"] or "geral",
            "priority": int(parsed["priority"]),
            "status": "todo",
            "due_at": due_utc.isoformat(),
            "estimated_minutes": int(parsed["estimated"]),
            "recurrence": parsed["recurrence"],
            "recur_interval": int(parsed["recur_interval"]),
            "recur_weekdays": parsed["recur_weekdays"],
        }
        try:
            sb.table("items").insert(item).execute()
            st.success("Criado")
        except Exception as e:
            st.error(f"Erro: {e}")
