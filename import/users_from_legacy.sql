-- Перенос учётных записей из старой базы.
--
-- Хеши паролей переносятся как есть: алгоритм тот же (PBKDF2-SHA256,
-- 200 000 итераций), поэтому пользователи входят со своими прежними
-- паролями. Сами пароли нигде не хранятся и восстановлению не подлежат.
CREATE EXTENSION IF NOT EXISTS dblink;

INSERT INTO users (login, password_hash, full_name, role, is_active, last_login_at)
SELECT l.login, l.password_hash, l.full_name, l.role, l.is_active, l.last_login_at
FROM dblink(
    'dbname=legacy user=e13',
    'select login, password_hash, full_name, role, is_active, last_login_at from users'
) AS l(
    login         text,
    password_hash text,
    full_name     text,
    role          text,
    is_active     boolean,
    last_login_at timestamptz
)
-- Повторный запуск не плодит дублей: логин уникален
WHERE NOT EXISTS (SELECT 1 FROM users u WHERE u.login = l.login);

SELECT login, full_name, role, is_active FROM users ORDER BY login;
