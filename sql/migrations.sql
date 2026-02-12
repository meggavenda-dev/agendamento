
-- Ajustes de profiles
alter table if exists public.profiles
  add column if not exists timezone text default 'America/Sao_Paulo',
  add column if not exists theme text default 'zen',
  add column if not exists email_notifications boolean default true,
  add column if not exists whatsapp_notifications boolean default false,
  add column if not exists whatsapp_number text,
  add column if not exists auto_rollover_enabled boolean default true,
  add column if not exists auto_bump_priority boolean default true;

-- Ajustes de items
alter table if exists public.items
  add column if not exists type text default 'task',
  add column if not exists tag text default 'geral',
  add column if not exists priority int default 3,
  add column if not exists status text default 'todo',
  add column if not exists estimated_minutes int default 30,
  add column if not exists spent_minutes int default 0,
  add column if not exists recurrence text default 'none',
  add column if not exists recur_interval int default 1,
  add column if not exists recur_weekdays text,
  add column if not exists recur_until timestamptz;

-- Reminders
create table if not exists public.reminders (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null,
  item_id uuid references public.items(id) on delete cascade,
  remind_at timestamptz not null,
  channel text not null,
  sent_at timestamptz
);

-- Inbox
create table if not exists public.inbox_notifications (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null,
  title text not null,
  body text,
  source text,
  item_id uuid,
  created_at timestamptz default now()
);

-- Tags
create table if not exists public.tags (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null,
  name text not null,
  icon text,
  color text,
  default_priority int,
  default_estimated_minutes int,
  default_type text
);
create unique index if not exists tags_user_name_ux on public.tags(user_id, name);
