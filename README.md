# 📌 Captação de Clínicas – CRM de Visitas (Streamlit + Supabase)

Este pacote é uma **refatoração estrutural** do seu MVP: separa UI (pages), regras de negócio (services), acesso a dados (db), e utilitários determinísticos (core).

## ✅ Como rodar

1) Crie e ative um virtualenv

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate
```

2) Instale dependências

```bash
pip install -r requirements.txt
```

3) Configure os secrets do Streamlit

Crie o arquivo:

`.streamlit/secrets.toml`

com:

```toml
SUPABASE_URL = "https://..."
SUPABASE_KEY = "..."
TIMEZONE = "America/Sao_Paulo"
```

4) Rode

```bash
streamlit run app.py
```

## 🧠 Notas de arquitetura

- `pages/` só contém UI.
- `services/` contém regras de negócio (ex.: status progressivo da clínica).
- `db/` encapsula Supabase e **sempre retorna dados** ou lança exceção.
- `core/` contém lógica pura (scheduler e tempo).

## ⚠️ Dívida técnica conhecida

Concorrência de agendamento (duas abas/usuários criando visitas no mesmo slot) ainda depende de uma verificação final server-side/constraint no Postgres.
