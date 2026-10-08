-- Перенос оборудования из старой базы (legacy) в текущую.
--
-- Сложность в том, что id площадок в новой базе свои: при переносе
-- они получили новые номера. Поэтому в legacy берём код площадки,
-- а здесь по нему находим её настоящий id.
CREATE EXTENSION IF NOT EXISTS dblink;

INSERT INTO chargers (
    station_id, name, vendor, model, serial, ocpp_id,
    power_kw, current_type, connectors, connector_count, tariff_rub,
    status, installed_at, warranty_until, last_service_at,
    service_interval_months, notes
)
SELECT
    s.id,                       -- id площадки уже в НАШЕЙ базе
    l.name, l.vendor, l.model, l.serial, l.ocpp_id,
    l.power_kw, l.current_type, l.connectors, l.connector_count, l.tariff_rub,
    l.status, l.installed_at, l.warranty_until, l.last_service_at,
    l.service_interval_months, l.notes
FROM dblink(
    'dbname=legacy user=e13',
    $$
    select st.code, c.name, c.vendor, c.model, c.serial, c.ocpp_id,
           c.power_kw, c.current_type, c.connectors, c.connector_count,
           c.tariff_rub, c.status, c.installed_at, c.warranty_until,
           c.last_service_at, c.service_interval_months, c.notes
    from chargers c
    join stations st on st.id = c.station_id
    $$
) AS l(
    station_code            text,
    name                    text,
    vendor                  text,
    model                   text,
    serial                  text,
    ocpp_id                 text,
    power_kw                numeric,
    current_type            text,
    connectors              text,
    connector_count         integer,
    tariff_rub              numeric,
    status                  text,
    installed_at            date,
    warranty_until          date,
    last_service_at         date,
    service_interval_months integer,
    notes                   text
)
JOIN stations s ON s.code = l.station_code
-- Повторный запуск не создаст дублей: серийный номер уже занят
WHERE NOT EXISTS (
    SELECT 1 FROM chargers c WHERE c.serial = l.serial AND l.serial <> ''
);

SELECT count(*) AS "оборудования в базе" FROM chargers;
