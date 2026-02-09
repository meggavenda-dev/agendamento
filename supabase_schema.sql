-- PulseAgenda (MVP) — Schema + RLS (Supabase Postgres)
-- Rode no Supabase SQL Editor

create extension if not exists "uuid-ossp";
create extension if not exists pgcrypto;

-- TYPES
create type if not exists public.item_type as enum ('task', 'meeting', 'event');
create type if not exists public.item_status as enum ('todo', 'doing', 'done', 'archived');
create type if not exists public.reminder_channel as enum ('in_app', 'email', 'whatsapp');

-- TABLES
create table if not exists public.profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  display_name text,
  email text,
  timezone text default 'America/Sao_Paulo',
  theme text default 'zen',
  work_start time default '08:00',
  work_end time default '18:00',
  email_notifications boolean default true,
  whatsapp_notifications boolean default false,
  whatsapp_number text,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

create table if not exists public.items (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  type public.item_type not null default 'task',
  title text not null,
  notes text,
  tag text default 'geral',
  priority int not null default 2,
  status public.item_status not null default 'todo',
  start_at timestamptz,
  due_at timestamptz,
  end_at timestamptz,
  estimated_minutes int default 15,
  checklist_enabled boolean default false,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

create table if not exists public.checklist_items (
  id uuid primary key default gen_random_uuid(),
  item_id uuid not null references public.items(id) on delete cascade,
  text text not null,
  done boolean default false,
  position int default 0,
  created_at timestamptz default now()
);

create table if not exists public.reminders (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  item_id uuid references public.items(id) on delete cascade,
  remind_at timestamptz not null,
  channel public.reminder_channel not null default 'in_app',
  payload jsonb default '{}'::jsonb,
  sent_at timestamptz,
  created_at timestamptz default now()
);

create table if not exists public.inbox_notifications (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  title text not null,
  body text,
  source text default 'reminder',
  item_id uuid references public.items(id) on delete set null,
  created_at timestamptz default now(),
  read_at timestamptz
);

-- INDEXES
create index if not exists profiles_email_idx on public.profiles(email);
create index if not exists items_user_idx on public.items(user_id);
create index if not exists items_due_idx on public.items(user_id, due_at);
create index if not exists items_status_idx on public.items(user_id, status);
create index if not exists checklist_item_idx on public.checklist_items(item_id);
create index if not exists reminders_due_idx on public.reminders(user_id, remind_at) where sent_at is null;
create index if not exists inbox_unread_idx on public.inbox_notifications(user_id, read_at) where read_at is null;

-- updated_at trigger
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

drop trigger if exists trg_items_updated_at on public.items;
create trigger trg_items_updated_at
before update on public.items
for each row execute function public.set_updated_at();

-- RLS
alter table public.profiles enable row level security;
alter table public.items enable row level security;
alter table public.checklist_items enable row level security;
alter table public.reminders enable row level security;
alter table public.inbox_notifications enable row level security;

-- POLICIES: profiles
create policy if not exists profiles_select_own
on public.profiles for select
using (id = auth.uid());

create policy if not exists profiles_insert_own
on public.profiles for insert
with check (id = auth.uid());

create policy if not exists profiles_update_own
on public.profiles for update
using (id = auth.uid())
with check (id = auth.uid());

-- POLICIES: items
create policy if not exists items_select_own
on public.items for select
using (user_id = auth.uid());

create policy if not exists items_insert_own
on public.items for insert
with check (user_id = auth.uid());

create policy if not exists items_update_own
on public.items for update
using (user_id = auth.uid())
with check (user_id = auth.uid());

create policy if not exists items_delete_own
on public.items for delete
using (user_id = auth.uid());

-- POLICIES: checklist_items (via vínculo com items)
create policy if not exists checklist_select_own
on public.checklist_items for select
using (exists (
  select 1 from public.items i
  where i.id = checklist_items.item_id
  and i.user_id = auth.uid()
));

create policy if not exists checklist_insert_own
on public.checklist_items for insert
with check (exists (
  select 1 from public.items i
  where i.id = checklist_items.item_id
  and i.user_id = auth.uid()
));

create policy if not exists checklist_update_own
on public.checklist_items for update
using (exists (
  select 1 from public.items i
  where i.id = checklist_items.item_id
  and i.user_id = auth.uid()
))
with check (exists (
  select 1 from public.items i
  where i.id = checklist_items.item_id
  and i.user_id = auth.uid()
));

create policy if not exists checklist_delete_own
on public.checklist_items for delete
using (exists (
  select 1 from public.items i
  where i.id = checklist_items.item_id
  and i.user_id = auth.uid()
));

-- POLICIES: reminders
create policy if not exists reminders_select_own
on public.reminders for select
using (user_id = auth.uid());

create policy if not exists reminders_insert_own
on public.reminders for insert
with check (user_id = auth.uid());

create policy if not exists reminders_update_own
on public.reminders for update
using (user_id = auth.uid())
with check (user_id = auth.uid());

create policy if not exists reminders_delete_own
on public.reminders for delete
using (user_id = auth.uid());

-- POLICIES: inbox_notifications
create policy if not exists inbox_select_own
on public.inbox_notifications for select
using (user_id = auth.uid());

create policy if not exists inbox_update_own
on public.inbox_notifications for update
using (user_id = auth.uid())
with check (user_id = auth.uid());
