-- Schema for TribunalUDC - Supabase PostgreSQL
-- Run this in the Supabase SQL Editor
-- Safe to re-run: drops and recreates everything (except auth.users)

-- Drop tables in reverse dependency order
drop table if exists disponibilidad cascade;
drop table if exists tfgs cascade;
drop table if exists periodos cascade;
drop table if exists docentes cascade;
drop table if exists profiles cascade;

-- Drop trigger if exists
drop trigger if exists on_auth_user_created on auth.users;
drop function if exists public.handle_new_user();

-- Profiles table (extends auth.users)
create table profiles (
  id uuid references auth.users on delete cascade primary key,
  nombre text not null,
  email text not null,
  rol text not null default 'DOCENTE' check (rol in ('ADMIN', 'DOCENTE')),
  created_at timestamptz default now()
);

-- Docentes
create table docentes (
  id uuid default gen_random_uuid() primary key,
  user_id uuid references auth.users on delete set null unique,
  nombre text not null,
  email text,
  departamento text,
  categoria text,
  antiguedad integer default 0,
  acepta_ingles boolean default false,
  activo boolean default true,
  created_at timestamptz default now()
);

-- Periodos de defensa
create table periodos (
  id uuid default gen_random_uuid() primary key,
  nombre text not null,
  fecha_inicio date not null,
  fecha_fin date not null,
  duracion_defensa integer default 30,
  estado text default 'BORRADOR' check (estado in ('BORRADOR', 'ABIERTO', 'CERRADO', 'GENERADO', 'PUBLICADO')),
  num_miembros integer default 3,
  max_tribunales integer default 5,
  created_at timestamptz default now()
);

-- Disponibilidad
create table disponibilidad (
  id uuid default gen_random_uuid() primary key,
  docente_id uuid references docentes(id) on delete cascade,
  periodo_id uuid references periodos(id) on delete cascade,
  dia_semana text not null,
  hora_inicio text not null,
  created_at timestamptz default now(),
  unique(docente_id, periodo_id, dia_semana, hora_inicio)
);

-- TFGs
create table tfgs (
  id uuid default gen_random_uuid() primary key,
  titulo text not null,
  estudiante text not null,
  tutor_id uuid references docentes(id),
  mencion text,
  idioma text default 'Castellano',
  titulacion text,
  created_at timestamptz default now()
);

-- Enable RLS
alter table profiles enable row level security;
alter table docentes enable row level security;
alter table periodos enable row level security;
alter table disponibilidad enable row level security;
alter table tfgs enable row level security;

-- Policies: authenticated users can read all
create policy "Authenticated can read profiles" on profiles for select to authenticated using (true);
create policy "Authenticated can read docentes" on docentes for select to authenticated using (true);
create policy "Authenticated can read periodos" on periodos for select to authenticated using (true);
create policy "Authenticated can read disponibilidad" on disponibilidad for select to authenticated using (true);
create policy "Authenticated can read tfgs" on tfgs for select to authenticated using (true);

-- Policies: admins can do everything (check via profiles.rol)
create policy "Admins can insert docentes" on docentes for insert to authenticated
  with check (exists (select 1 from profiles where profiles.id = auth.uid() and profiles.rol = 'ADMIN'));
create policy "Admins can update docentes" on docentes for update to authenticated
  using (exists (select 1 from profiles where profiles.id = auth.uid() and profiles.rol = 'ADMIN'));
create policy "Admins can delete docentes" on docentes for delete to authenticated
  using (exists (select 1 from profiles where profiles.id = auth.uid() and profiles.rol = 'ADMIN'));

create policy "Admins can insert periodos" on periodos for insert to authenticated
  with check (exists (select 1 from profiles where profiles.id = auth.uid() and profiles.rol = 'ADMIN'));
create policy "Admins can update periodos" on periodos for update to authenticated
  using (exists (select 1 from profiles where profiles.id = auth.uid() and profiles.rol = 'ADMIN'));
create policy "Admins can delete periodos" on periodos for delete to authenticated
  using (exists (select 1 from profiles where profiles.id = auth.uid() and profiles.rol = 'ADMIN'));

create policy "Admins can insert tfgs" on tfgs for insert to authenticated
  with check (exists (select 1 from profiles where profiles.id = auth.uid() and profiles.rol = 'ADMIN'));
create policy "Admins can update tfgs" on tfgs for update to authenticated
  using (exists (select 1 from profiles where profiles.id = auth.uid() and profiles.rol = 'ADMIN'));
create policy "Admins can delete tfgs" on tfgs for delete to authenticated
  using (exists (select 1 from profiles where profiles.id = auth.uid() and profiles.rol = 'ADMIN'));

-- Disponibilidad: docentes can manage their own (via user_id link in docentes)
create policy "Users can insert own disponibilidad" on disponibilidad for insert to authenticated
  with check (
    exists (select 1 from docentes where docentes.id = docente_id and docentes.user_id = auth.uid())
    or exists (select 1 from profiles where profiles.id = auth.uid() and profiles.rol = 'ADMIN')
  );
create policy "Users can update own disponibilidad" on disponibilidad for update to authenticated
  using (
    exists (select 1 from docentes where docentes.id = docente_id and docentes.user_id = auth.uid())
    or exists (select 1 from profiles where profiles.id = auth.uid() and profiles.rol = 'ADMIN')
  );
create policy "Users can delete own disponibilidad" on disponibilidad for delete to authenticated
  using (
    exists (select 1 from docentes where docentes.id = docente_id and docentes.user_id = auth.uid())
    or exists (select 1 from profiles where profiles.id = auth.uid() and profiles.rol = 'ADMIN')
  );

-- Auto-create profile on signup
create or replace function public.handle_new_user()
returns trigger as $$
begin
  insert into public.profiles (id, nombre, email, rol)
  values (new.id, coalesce(new.raw_user_meta_data->>'nombre', split_part(new.email, '@', 1)), new.email, 'DOCENTE');
  return new;
end;
$$ language plpgsql security definer;

create trigger on_auth_user_created
  after insert on auth.users
  for each row execute procedure public.handle_new_user();
