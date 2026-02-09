# -*- coding: utf-8 -*-
import streamlit as st


def badge(label: str, color: str = "#0F6CBD"):
    st.markdown(
        f"<span style='background:{color};color:white;padding:2px 8px;border-radius:999px;font-size:0.85em'>{label}</span>",
        unsafe_allow_html=True,
    )


def money(v):
    if v is None:
        return "—"
    try:
        v = float(v)
    except Exception:
        return str(v)
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def pct(v):
    if v is None:
        return "—"
    try:
        v = float(v)
    except Exception:
        return str(v)
    return f"{v*100:.0f}%"
