-- Migracion incremental para conectar la app con el solver MILP.
-- Ejecutar en el SQL Editor de Supabase sobre una base de datos ya existente.
-- (schema.sql borra y recrea todo; esta migracion conserva los datos.)

-- 1) Configuracion del periodo que necesita el generador de slots
alter table periodos add column if not exists hora_inicio_dia text not null default '09:00';
alter table periodos add column if not exists hora_fin_dia    text not null default '14:00';
alter table periodos add column if not exists num_aulas       integer      default 3;

-- 2) La disponibilidad pasa de dia de la semana a fecha concreta.
--    Si tu tabla ya tiene 'fecha', estos pasos no hacen nada.
alter table disponibilidad add column if not exists fecha date;

do $$
begin
  if exists (
    select 1 from information_schema.columns
    where table_name = 'disponibilidad' and column_name = 'dia_semana'
  ) then
    -- Las filas antiguas guardaban un dia de la semana, no una fecha:
    -- no se pueden convertir, hay que volver a pedir la disponibilidad.
    delete from disponibilidad where fecha is null;
    alter table disponibilidad drop constraint if exists disponibilidad_docente_id_periodo_id_dia_semana_hora_inicio_key;
    alter table disponibilidad drop column dia_semana;
  end if;
end $$;

alter table disponibilidad alter column fecha set not null;

alter table disponibilidad drop constraint if exists disponibilidad_docente_periodo_fecha_hora_key;
alter table disponibilidad add constraint disponibilidad_docente_periodo_fecha_hora_key
  unique (docente_id, periodo_id, fecha, hora_inicio);

create index if not exists disponibilidad_periodo_idx on disponibilidad (periodo_id);
create index if not exists disponibilidad_docente_periodo_idx on disponibilidad (docente_id, periodo_id);
