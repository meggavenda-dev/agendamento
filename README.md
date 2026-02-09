# Captação de Clínicas — CRM de Conversão (Streamlit + Supabase)

Este projeto é um **CRM focado em conversão** para captação e relacionamento com clínicas: **funil**, **priorização**, **alertas**, **visitas**, **tarefas** e **relatórios**.

## Como rodar

### 1) Banco (Supabase)
1. Crie um projeto no Supabase.
2. Abra o **SQL Editor** e execute o arquivo: `supabase/migrations/001_schema.sql`.

### 2) Secrets do Streamlit
Crie `.streamlit/secrets.toml` (não versionar) com:

```toml
SUPABASE_URL = "https://xxxx.supabase.co"
SUPABASE_KEY = "<service_role_or_anon_key>"
TIMEZONE = "America/Sao_Paulo"
ALERT_NO_CONTACT_DAYS = 14
```

> Para MVP interno, usar `service_role` simplifica (sem RLS). Em produção, use autenticação + RLS.

### 3) Executar

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Estrutura

- `app.py` — entrada do app
- `pages/` — telas
- `src/db.py` — acesso ao Supabase
- `src/scheduler.py` — grade de horários
- `src/importers.py` — importação de clínicas via Excel
- `supabase/migrations/001_schema.sql` — schema

## Observações
- Kanban: MVP sem drag&drop (Streamlit puro). Você move o card por seletor.
- Alertas: baseados em `next_action_due`, `ata_finalized`, `interest_level` e `probability`.
