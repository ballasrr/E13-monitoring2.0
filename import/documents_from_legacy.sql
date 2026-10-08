-- Перенос карточек документов из старой базы.
--
-- Площадки связываем по коду: id в двух базах разные.
-- supersedes_id не переносим — он ссылается на id старой базы, а цепочку
-- редакций и так задают series_id с version.
-- uploaded_by_id оставляем пустым: учётки могли не переехать.
CREATE EXTENSION IF NOT EXISTS dblink;

INSERT INTO documents (
    station_id, doc_type, title, description, doc_number, doc_date, valid_until,
    original_name, stored_name, mime, size_bytes, checksum,
    series_id, version, is_current, created_at, updated_at
)
SELECT
    s.id,
    l.doc_type, l.title, l.description, l.doc_number, l.doc_date, l.valid_until,
    l.original_name, l.stored_name, l.mime, l.size_bytes, l.checksum,
    l.series_id, l.version, l.is_current, l.created_at, l.updated_at
FROM dblink(
    'dbname=legacy user=e13',
    $$
    select st.code, d.doc_type, d.title, d.description, d.doc_number,
           d.doc_date, d.valid_until, d.original_name, d.stored_name,
           d.mime, d.size_bytes, d.checksum, d.series_id, d.version,
           d.is_current, d.created_at, d.updated_at
    from documents d
    join stations st on st.id = d.station_id
    $$
) AS l(
    station_code  text,
    doc_type      text,
    title         text,
    description   text,
    doc_number    text,
    doc_date      date,
    valid_until   date,
    original_name text,
    stored_name   text,
    mime          text,
    size_bytes    bigint,
    checksum      text,
    series_id     bigint,
    version       integer,
    is_current    boolean,
    created_at    timestamptz,
    updated_at    timestamptz
)
JOIN stations s ON s.code = l.station_code
-- Повторный запуск не плодит дублей: имя файла в хранилище уникально
WHERE NOT EXISTS (
    SELECT 1 FROM documents d WHERE d.stored_name = l.stored_name
);

-- Номера серий перенесены как есть, поэтому счётчик надо сдвинуть:
-- иначе следующий загруженный документ получит занятый номер.
SELECT setval(
    'document_series_seq',
    GREATEST((SELECT COALESCE(MAX(series_id), 0) FROM documents), 1)
);

SELECT count(*) AS "документов", count(DISTINCT series_id) AS "серий" FROM documents;
