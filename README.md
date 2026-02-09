# PulseAgenda (MVP) — Streamlit + Supabase + GitHub Actions + Twilio + Gmail

**Tagline:** Seu ritmo. Seu foco. Sua agenda.

Este repositório contém um MVP **mobile-first** (tema Zen) com:
- Login com Google via Supabase Auth
- Tarefas/Reuniões/Eventos (tabela `items`)
- Tela **Agora** (atrasadas + próximas 24h + prioridades)
- Tela **Semana** com **scroll horizontal por dias** e **destaque do dia de hoje** (borda azul suave)
- Notificações: **in-app + e-mail (Gmail SMTP) + WhatsApp (Twilio Sandbox)** via **GitHub Actions (cron)**

## 1) Pré-requisitos
- Projeto no Supabase
- Google OAuth configurado no Supabase Auth
- Twilio WhatsApp Sandbox configurado
- Gmail com **2FA** e **App Password** (para SMTP)

## 2) Variáveis/Segredos

### Streamlit Community Cloud → Secrets
Configure no painel do Streamlit Cloud:

```toml
SUPABASE_URL = "https://xxxx.supabase.co"
SUPABASE_ANON_KEY = "sua_anon_key"
SUPABASE_REDIRECT_URL = "https://SEUAPP.streamlit.app/?auth=callback"
```

### GitHub → Actions Secrets
Em **Settings → Secrets and variables → Actions**:
- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`
- `TWILIO_ACCOUNT_SID`
- `TWILIO_AUTH_TOKEN`
- `TWILIO_WHATSAPP_FROM` (ex: `whatsapp:+14155238886` no sandbox)
- `GMAIL_USER` (ex: `guilherme.h.cavalcante@gmail.com`)
- `GMAIL_APP_PASSWORD` (App Password do Gmail)

## 3) Supabase — Patch SQL (profiles.email)
No Supabase SQL Editor:

```sql
alter table public.profiles add column if not exists email text;
create index if not exists profiles_email_idx on public.profiles(email);

create or replace function public.set_updated_at()
returns trigger as $$
begin
  new.updated_at = now();
  return new;
end;
$$ language plpgsql;

drop trigger if exists trg_profiles_updated_at on public.profiles;
create trigger trg_profiles_updated_at
before update on public.profiles
for each row execute function public.set_updated_at();
```

> Observação: as tabelas e políticas RLS (items/reminders/inbox etc.) devem existir no Supabase.

## 4) Deploy (Streamlit Community Cloud)
- Crie um app apontando para `app.py`
- Configure os Secrets
- Deploy ✅

## 5) Scheduler de lembretes
O workflow `.github/workflows/reminders.yml` roda a cada 5 minutos e dispara lembretes vencidos.

## 6) WhatsApp Sandbox
- Entre no Sandbox com o join code do Twilio
- Em **Config** (no app), habilite WhatsApp e salve seu número no formato `+55DDDNUMERO`
