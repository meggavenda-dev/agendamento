from __future__ import annotations

import streamlit as st
from supabase import create_client


class DBError(RuntimeError):
    pass


@st.cache_resource
def get_supabase():
    url = (st.secrets.get("SUPABASE_URL") or "").strip()
    key = (st.secrets.get("SUPABASE_KEY") or "").strip()
    if not url or not key:
        raise DBError("Faltam SUPABASE_URL e/ou SUPABASE_KEY nos Secrets.")
    return create_client(url, key)


def data_or_raise(res, action: str):
    """Padroniza retorno: sempre .data ou DBError."""
    err = getattr(res, "error", None)
    if err:
        raise DBError(f"Supabase erro em {action}: {err}")
    try:
        return res.data
    except Exception as e:
        raise DBError(f"Falha ao obter retorno de {action}: {e}") from e
