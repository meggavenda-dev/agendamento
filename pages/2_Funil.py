# -*- coding: utf-8 -*-
import streamlit as st

from src.db import clinics_list, clinics_update
from src.constants import KANBAN_COLUMNS, INTEREST_LEVELS
from src.ui import money, pct

st.header("Funil Comercial (Kanban)")
st.caption("MVP sem drag&drop: mova a clínica pelo seletor 'Mover para'.")

c1, c2, c3 = st.columns([1,1,1])
with c1:
    only_hot = st.checkbox("Mostrar apenas quentes", value=False)
with c2:
    interest = st.selectbox("Interesse", [""] + INTEREST_LEVELS)
with c3:
    min_prob = st.slider("Probabilidade mínima", 0.0, 1.0, 0.0, 0.05)

res = clinics_list().data or []

if only_hot:
    res = [x for x in res if (x.get("interest_level") == "Alto") or (x.get("probability") or 0) >= 0.70]
if interest:
    res = [x for x in res if x.get("interest_level") == interest]
res = [x for x in res if (x.get("probability") or 0) >= min_prob]

by = {k: [] for k in KANBAN_COLUMNS}
for c in res:
    col = c.get("lead_status") or "Novo"
    if col not in by:
        col = "Novo"
    by[col].append(c)

cols = st.columns(len(KANBAN_COLUMNS))
for i, status in enumerate(KANBAN_COLUMNS):
    with cols[i]:
        st.subheader(status)
        st.caption(f"{len(by[status])} clínica(s)")
        for c in by[status][:80]:
            st.markdown(f"**{c['clinic_id']} — {c.get('trade_name') or c.get('legal_name')}**")
            st.write(f"Prob: {pct(c.get('probability'))} | Potencial: {money(c.get('potential_value'))}")
            st.write(f"Interesse: {c.get('interest_level')} | Próx ação: {c.get('next_action') or '—'}")
            new = st.selectbox(
                "Mover para",
                KANBAN_COLUMNS,
                index=KANBAN_COLUMNS.index(status),
                key=f"move_{c['clinic_id']}_{status}",
            )
            if new != status:
                if st.button("Aplicar", key=f"apply_{c['clinic_id']}_{status}"):
                    clinics_update(int(c["clinic_id"]), {"lead_status": new})
                    st.success("Movido!")
                    st.rerun()
            st.divider()
