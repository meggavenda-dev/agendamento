# -*- coding: utf-8 -*-
import streamlit as st

st.header("Configuração")

st.markdown("""
## Secrets necessários
- `SUPABASE_URL`
- `SUPABASE_KEY`
- `TIMEZONE` (ex: `America/Sao_Paulo`)

## Dicas
- Para MVP interno, você pode usar `service_role`.
- Para produção, habilite autenticação e RLS.
""")
