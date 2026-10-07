-- Перенос площадок из старой базы (legacy) в текущую.
--
-- dblink позволяет сходить запросом в другую базу того же сервера.
-- Расширение входит в стандартную поставку Postgres, ставится один раз.
CREATE EXTENSION IF NOT EXISTS dblink;

INSERT INTO stations (code, name, status, lat, lng, address, archived)
SELECT code, name, status, lat, lng, address, archived
FROM dblink(
    'dbname=legacy user=e13',
    'select code, name, status, lat, lng, address, archived from stations'
) AS legacy_stations(
    code    text,
    name    text,
    status  text,
    lat     numeric,
    lng     numeric,
    address text,
    archived boolean
)
-- Повторный запуск не создаст дублей
ON CONFLICT DO NOTHING;

SELECT count(*) AS "перенесено площадок" FROM stations;
