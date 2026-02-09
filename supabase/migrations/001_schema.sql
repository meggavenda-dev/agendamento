-- 001_schema.sql
-- CRM de Conversão — Captação de Clínicas
-- Rode este arquivo no SQL Editor do Supabase.

create extension if not exists pgcrypto;

-- Clinics
create table if not exists public.clinics (
  clinic_id bigint primary key,
  legal_name text not null,
  trade_name text,
  cnpj text,

  clinic_type text,
  specialties text[],
  volume_monthly int,

  -- comercial
  lead_status text not null default 'Novo',
  interest_level text not null default 'Médio',
  probability numeric(5,4) not null default 0.30,
  potential_value numeric(12,2),
  competitor text,
  loss_reason text,

  -- decisão/próxima ação
  last_contact_at timestamptz,
  next_action text,
  next_action_due date,

  decisor_name text,
  decisor_role text,
  decisor_phone text,
  decisor_whatsapp text,
  decisor_email text,

  phone text,
  email text,
  website text,

  address_street text,
  address_number text,
  address_complement text,
  address_district text,
  address_city text,
  address_state text,
  address_zip text,

  region text,
  notes text,

  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists clinics_lead_status_idx on public.clinics (lead_status);
create index if not exists clinics_next_action_due_idx on public.clinics (next_action_due);
create index if not exists clinics_probability_idx on public.clinics (probability);

-- updated_at trigger function
create or replace function public.set_updated_at()
returns trigger language plpgsql as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

drop trigger if exists trg_clinics_updated_at on public.clinics;
create trigger trg_clinics_updated_at
before update on public.clinics
for each row execute function public.set_updated_at();

-- Visits
create table if not exists public.visits (
  visit_id bigserial primary key,
  clinic_id bigint not null references public.clinics(clinic_id) on delete cascade,

  start_at timestamptz not null,
  end_at timestamptz not null,
  status text not null default 'Agendado',

  visit_type text,
  objective text,
  duration_minutes int,
  cancel_reason text,

  summary text,
  discussion_rich text,
  next_steps text,
  ata_finalized boolean not null default false,

  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists visits_clinic_id_idx on public.visits (clinic_id);
create index if not exists visits_start_at_idx on public.visits (start_at);

drop trigger if exists trg_visits_updated_at on public.visits;
create trigger trg_visits_updated_at
before update on public.visits
for each row execute function public.set_updated_at();

-- Visit participants
create table if not exists public.visit_participants (
  participant_id bigserial primary key,
  visit_id bigint not null references public.visits(visit_id) on delete cascade,

  name text not null,
  title text,
  influence text,
  decision_role text,

  created_at timestamptz not null default now()
);

create index if not exists visit_participants_visit_id_idx on public.visit_participants (visit_id);

-- Visit history
create table if not exists public.visit_history (
  id bigserial primary key,
  visit_id bigint not null references public.visits(visit_id) on delete cascade,
  action text not null,
  old jsonb,
  new jsonb,
  created_at timestamptz not null default now()
);

create index if not exists visit_history_visit_id_idx on public.visit_history (visit_id);

-- Tasks
create table if not exists public.tasks (
  task_id bigserial primary key,
  clinic_id bigint not null references public.clinics(clinic_id) on delete cascade,
  visit_id bigint references public.visits(visit_id) on delete set null,

  title text not null,
  description text,

  due_date date,
  status text not null default 'Pendente',
  priority int not null default 2,
  impact text,
  owner text,

  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists tasks_due_date_idx on public.tasks (due_date);
create index if not exists tasks_clinic_id_idx on public.tasks (clinic_id);

drop trigger if exists trg_tasks_updated_at on public.tasks;
create trigger trg_tasks_updated_at
before update on public.tasks
for each row execute function public.set_updated_at();

-- Settings
create table if not exists public.settings (
  key text primary key,
  value jsonb not null,
  updated_at timestamptz not null default now()
);

insert into public.settings(key, value)
values (
  'scheduler',
  '{"slot_minutes":15,"visit_default_minutes":45,"work_start":"08:00","work_end":"18:00","grid_columns":4}'::jsonb
)
on conflict (key) do nothing;

-- RLS: para MVP interno, use service_role.
-- Em produção, habilite RLS e crie policies por usuário.
