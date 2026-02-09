# -*- coding: utf-8 -*-
import streamlit as st


def apply_style():
    st.markdown(
        """
<style>
  .block-container { padding-top: 1.1rem; padding-bottom: 2.2rem; }

  /* Typography */
  h1, h2, h3 { letter-spacing: -0.02em; }
  h1 { font-size: 2.0rem; }

  /* Sidebar */
  [data-testid="stSidebar"] {
    background: #FFFFFF;
    border-right: 1px solid rgba(15, 23, 42, 0.08);
  }

  /* Cards */
  .card {
    background: #ffffff;
    border: 1px solid rgba(15, 23, 42, 0.08);
    border-radius: 16px;
    padding: 14px 16px;
    box-shadow: 0 10px 28px rgba(15, 23, 42, 0.06);
  }
  .card-title { font-weight: 700; margin: 0 0 0.35rem 0; }
  .muted { color: rgba(15, 23, 42, 0.62); font-size: 0.92rem; }

  /* Pills */
  .pill {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 999px;
    font-size: 0.82rem;
    font-weight: 700;
    color: white;
    margin-left: 6px;
  }
  .pill.red { background:#DC2626; }
  .pill.yellow { background:#F59E0B; }
  .pill.green { background:#16A34A; }
  .pill.blue { background:#2563EB; }

  /* Metric cards (Streamlit metrics look better with spacing) */
  [data-testid="stMetric"] {
    background: #FFFFFF;
    border: 1px solid rgba(15, 23, 42, 0.08);
    padding: 12px 14px;
    border-radius: 16px;
  }

  /* Dataframe rounding */
  .stDataFrame { border-radius: 14px; overflow: hidden; }
</style>
        """,
        unsafe_allow_html=True,
    )


def card_open():
    st.markdown("<div class='card'>", unsafe_allow_html=True)


def card_close():
    st.markdown("</div>", unsafe_allow_html=True)
