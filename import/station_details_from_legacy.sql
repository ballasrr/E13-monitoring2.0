-- Дозаполнение площадок из старой базы.
--
-- Строки уже созданы предыдущим переносом, поэтому здесь UPDATE, а не INSERT:
-- дописываем колонки, которых в модели не было, когда переносили первый раз.
-- Связываем по коду площадки — id в двух базах разные.
CREATE EXTENSION IF NOT EXISTS dblink;

UPDATE stations s SET
    region              = l.region,
    site_type           = l.site_type,
    land_status         = l.land_status,
    landlord            = l.landlord,
    opened_at           = l.opened_at,
    grid_company        = l.grid_company,
    tp_number           = l.tp_number,
    transformer_kva     = l.transformer_kva,
    allocated_kw        = l.allocated_kw,
    voltage             = l.voltage,
    connection_contract = l.connection_contract,
    connection_date     = l.connection_date,
    meter_number        = l.meter_number,
    energy_supplier     = l.energy_supplier,
    has_canopy          = l.has_canopy,
    has_lighting        = l.has_lighting,
    has_cctv            = l.has_cctv,
    has_internet        = l.has_internet,
    internet_type       = l.internet_type,
    has_fence           = l.has_fence,
    has_wc              = l.has_wc,
    has_cafe            = l.has_cafe,
    has_signage         = l.has_signage,
    accessible          = l.accessible,
    parking_spots       = l.parking_spots,
    surface_type        = l.surface_type,
    has_operator        = l.has_operator,
    staff_count         = l.staff_count,
    work_schedule       = l.work_schedule,
    responsible_name    = l.responsible_name,
    responsible_phone   = l.responsible_phone,
    service_company     = l.service_company,
    notes               = l.notes,
    custom              = l.custom
FROM dblink(
    'dbname=legacy user=e13',
    $$
    select code, region, site_type, land_status, landlord, opened_at,
           grid_company, tp_number, transformer_kva, allocated_kw, voltage,
           connection_contract, connection_date, meter_number, energy_supplier,
           has_canopy, has_lighting, has_cctv, has_internet, internet_type,
           has_fence, has_wc, has_cafe, has_signage, accessible,
           parking_spots, surface_type,
           has_operator, staff_count, work_schedule,
           responsible_name, responsible_phone, service_company,
           notes, custom
    from stations
    $$
) AS l(
    code                text,
    region              text,
    site_type           text,
    land_status         text,
    landlord            text,
    opened_at           date,
    grid_company        text,
    tp_number           text,
    transformer_kva     numeric,
    allocated_kw        numeric,
    voltage             text,
    connection_contract text,
    connection_date     date,
    meter_number        text,
    energy_supplier     text,
    has_canopy          boolean,
    has_lighting        boolean,
    has_cctv            boolean,
    has_internet        boolean,
    internet_type       text,
    has_fence           boolean,
    has_wc              boolean,
    has_cafe            boolean,
    has_signage         boolean,
    accessible          boolean,
    parking_spots       integer,
    surface_type        text,
    has_operator        boolean,
    staff_count         integer,
    work_schedule       text,
    responsible_name    text,
    responsible_phone   text,
    service_company     text,
    notes               text,
    custom              jsonb
)
WHERE s.code = l.code;

SELECT code, tp_number, allocated_kw, has_cctv, responsible_name
FROM stations ORDER BY code LIMIT 5;
