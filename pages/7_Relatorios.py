# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

from src.db import clinics_list, visits_list_range

st.header("Relatórios")
st.caption("Relatórios básicos: funil, conversão, visitas e motivos de perda.")

clinics = (clinics_list(limit=5000).data or [])
if not clinics:
    st.info("Sem dados ainda.")
    st.stop()

df = pd.DataFrame(clinics)

st.subheader("Clínicas por etapa")
counts = df["lead_status"].fillna("Novo").value_counts()
fig, ax = plt.subplots(figsize=(8, 4))
counts.plot(kind="bar", ax=ax, color="#0F6CBD")
ax.set_xlabel("Etapa")
ax.set_ylabel("Quantidade")
ax.set_title("Distribuição por etapa")
st.pyplot(fig)

fechado = int((df["lead_status"] == "Fechado").sum())
perdido = int((df["lead_status"] == "Perdido").sum())
in_play = int((~df["lead_status"].isin(["Fechado", "Perdido"])) .sum())

c1, c2, c3 = st.columns(3)
c1.metric("Fechados", fechado)
c2.metric("Perdidos", perdido)
c3.metric("Em andamento", in_play)

st.subheader("Visitas por período")
colA, colB = st.columns(2)
with colA:
    start = st.date_input("Início", value=pd.Timestamp.today().normalize() - pd.Timedelta(days=30))
with colB:
    end = st.date_input("Fim", value=pd.Timestamp.today().normalize())

res = visits_list_range(f"{start}T00:00:00Z", f"{end}T23:59:59Z").data or []
if not res:
    st.info("Sem visitas no período.")
else:
    vdf = pd.DataFrame(res)
    vdf["start_at"] = pd.to_datetime(vdf["start_at"], utc=True)
    vdf["dia"] = vdf["start_at"].dt.date
    by_day = vdf.groupby("dia").size()

    fig2, ax2 = plt.subplots(figsize=(8, 4))
    by_day.plot(ax=ax2, color="#107C10")
    ax2.set_xlabel("Dia")
    ax2.set_ylabel("Visitas")
    ax2.set_title("Visitas por dia")
    st.pyplot(fig2)

st.subheader("Motivos de perda")
losses = df[df["lead_status"] == "Perdido"]["loss_reason"].fillna("(sem motivo)").value_counts().head(15)
if len(losses):
    st.dataframe(losses.reset_index().rename(columns={"index": "motivo", "loss_reason": "quantidade"}), use_container_width=True)
else:
    st.info("Nenhuma clínica marcada como Perdido.")
