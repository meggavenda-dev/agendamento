# Captação de Clínicas (Streamlit + Supabase)

MVP para acompanhar captação de novas clínicas, agendamento de visitas, registro de reuniões e tarefas.

## ✅ Regras implementadas
- Duração padrão da visita: **45 min**
- Slots sugeridos: **15 min** (configurável em `settings.scheduler`)
- Grade de horários sugeridos (08:00–18:00 por padrão, configurável)
- Modo livre: permite qualquer horário, **mas bloqueia conflito**
- Status da visita: `Agendado`, `Realizado`, `Reagendada`, `Fechado Parceria`, `Sem Parceria`
- Status da clínica: `Prospect`, `Em negociação`, `Ativo`, `Perdido`
- Automação:
  - Ao agendar a **primeira visita** de uma clínica que está em `Prospect` ⇒ vira `Em negociação`
  - Ao marcar visita como `Fechado Parceria` ⇒ clínica vira `Ativo`
  - Ao marcar visita como `Sem Parceria` ⇒ clínica vira `Perdido`

## 1) Banco (Supabase)
1. Crie um projeto no Supabase.
2. No SQL Editor, rode o script `supabase.sql`.

## 2) Configuração local
Crie `.streamlit/secrets.toml` (não commitar):

```toml
SUPABASE_URL="https://xxxx.supabase.co"
SUPABASE_KEY="sua_anon_key"
TIMEZONE="America/Sao_Paulo"
```

Instale dependências e rode:

```bash
pip install -r requirements.txt
streamlit run app.py
```

## 3) Deploy (Streamlit Community Cloud)
- Aponte para este repositório
- Configure as mesmas keys em **Secrets**
