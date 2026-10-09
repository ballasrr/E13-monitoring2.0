# Развёртывание на боевом сервере

Порядок проверен на Ubuntu 24.04. Выполняется один раз, занимает
примерно полтора часа вместе с переносом данных.

---

## 0. Что понадобится

| Что | Зачем | Минимум |
|---|---|---|
| Сервер | 2 ядра, 4 ГБ ОЗУ, 40 ГБ диска | этого хватит надолго |
| Домен | без него не будет HTTPS | например `api.e13.ru` |
| A-запись | домен → адрес сервера | сделать заранее, DNS расходится до часа |

Диск считайте по документам: сейчас 68 файлов, но сканы договоров
набегают быстро. 40 ГБ — запас на годы, расширить потом можно.

---

## 1. Защита сервера

Это делается **до** всего остального. Сервер с белым адресом начинают
перебирать по SSH в первые же минуты после включения.

```bash
# Под root, сразу после получения доступа
adduser e13
usermod -aG sudo e13
```

Со своей машины скопируйте ключ (если ключа нет — `ssh-keygen -t ed25519`):

```powershell
ssh-copy-id e13@АДРЕС_СЕРВЕРА
```

Убедитесь, что вход по ключу работает, **не закрывая текущую сессию**:
откройте второе окно и зайдите. Только после этого отключайте пароли:

```bash
sudo nano /etc/ssh/sshd_config
# PasswordAuthentication no
# PermitRootLogin no
sudo systemctl restart ssh
```

Файрвол:

```bash
sudo ufw allow OpenSSH
sudo ufw allow 80
sudo ufw allow 443
sudo ufw enable
sudo ufw status
```

Порт базы 5432 здесь не открывается и открывать его не нужно:
в боевой конфигурации база видна только изнутри Docker.

---

## 2. Docker

```bash
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker e13
```

Выйдите и зайдите заново, чтобы группа применилась. Проверка:

```bash
docker run --rm hello-world
```

---

## 3. Код и настройки

```bash
sudo mkdir -p /opt/e13-monitoring && sudo chown e13:e13 /opt/e13-monitoring
git clone ВАШ_РЕПОЗИТОРИЙ /opt/e13-monitoring
cd /opt/e13-monitoring

cp .env.prod.example .env
nano .env
```

Секреты генерируем, а не придумываем:

```bash
openssl rand -base64 24   # POSTGRES_PASSWORD
openssl rand -hex 48      # SECRET_KEY
openssl rand -base64 18   # FIRST_ADMIN_PASSWORD
```

**Пароль администратора задайте сразу.** Он применяется только при
первом запуске, когда в базе ещё никого нет. Эндпоинта смены пароля в
проекте нет — поменять потом можно будет только запросом в базу.
Пароль `asko2026` с рабочей машины на сервер переносить нельзя:
он короткий и предсказуемый, а сервер открыт всему интернету.

Поменять пароль уже после запуска можно так:

```bash
docker compose -f docker-compose.prod.yml exec api python scripts/set_password.py admin
```

Пароль вводится скрыто и в историю команд не попадает. Все текущие
сессии после смены завершаются.

---

## 4. Запуск

```bash
docker compose -f docker-compose.prod.yml up -d --build
docker compose -f docker-compose.prod.yml ps
```

Накатить схему базы:

```bash
docker compose -f docker-compose.prod.yml exec api alembic upgrade head
```

Проверить:

```bash
curl -i https://ВАШ_ДОМЕН/api/health
```

Должен прийти `200` и `{"status":"ok"}`. Сертификат Caddy получает сам
при первом обращении — если вместо этого ошибка, смотрите
`docker compose -f docker-compose.prod.yml logs caddy`: почти всегда
дело в том, что A-запись ещё не разошлась.

---

## 5. Перенос данных

С рабочей машины выгружаем, на сервер загружаем.

```powershell
# У себя
docker compose exec -T db pg_dump -U e13 -d e13_monitoring -Fc > e13.dump
docker compose exec -T api tar czf - -C /data uploads > uploads.tar.gz
scp e13.dump uploads.tar.gz e13@АДРЕС_СЕРВЕРА:/tmp/
```

```bash
# На сервере
cd /opt/e13-monitoring
docker compose -f docker-compose.prod.yml exec -T db \
  pg_restore -U e13 -d e13_monitoring --clean --if-exists < /tmp/e13.dump
docker compose -f docker-compose.prod.yml exec -T api \
  tar xzf - -C /data < /tmp/uploads.tar.gz
docker compose -f docker-compose.prod.yml restart api
```

Проверьте, что всё доехало:

```bash
docker compose -f docker-compose.prod.yml exec db psql -U e13 -d e13_monitoring \
  -c "select (select count(*) from stations) as площадок,
             (select count(*) from chargers) as зарядок,
             (select count(*) from documents) as документов;"
```

Должно совпасть с тем, что было у вас: 15 площадок, 28 зарядок,
66 документов.

---

## 6. Резервные копии

```bash
mkdir -p /var/backups/e13
cd /opt/e13-monitoring && ./scripts/backup.sh
crontab -e
```

Добавить строку:

```
30 3 * * * cd /opt/e13-monitoring && ./scripts/backup.sh >> /var/log/e13-backup.log 2>&1
```

Хранится 14 дней, дальше старое удаляется само.

**Копии на том же сервере — это не копии.** Диск умрёт вместе с ними.
Настройте выгрузку в другое место: `rclone` в облако, `scp` на вторую
машину или на ваш компьютер по расписанию.

### Восстановление

Проверьте эту процедуру **сейчас**, пока ничего не потеряно.
Копия, которую ни разу не разворачивали, копией не является.

```bash
cd /opt/e13-monitoring
docker compose -f docker-compose.prod.yml exec -T db \
  pg_restore -U e13 -d e13_monitoring --clean --if-exists < /var/backups/e13/db-ДАТА.dump
docker compose -f docker-compose.prod.yml exec -T api \
  tar xzf - -C /data < /var/backups/e13/uploads-ДАТА.tar.gz
docker compose -f docker-compose.prod.yml restart api
```

---

## 7. Обновление

```bash
cd /opt/e13-monitoring
git pull
docker compose -f docker-compose.prod.yml up -d --build
docker compose -f docker-compose.prod.yml exec api alembic upgrade head
```

Перед обновлением со сменой схемы базы делайте копию: `./scripts/backup.sh`.
Откат миграции бывает невозможен, если она удаляла колонку.

---

## 8. Что смотреть, когда что-то не так

```bash
# Логи приложения
docker compose -f docker-compose.prod.yml logs api --tail 100

# Логи веб-сервера и выдачи сертификата
docker compose -f docker-compose.prod.yml logs caddy --tail 50

# Кто сколько занимает
docker compose -f docker-compose.prod.yml ps
df -h
docker system df
```

Если кончается место — чаще всего виноваты старые образы Docker:
`docker system prune -a` (тома с данными не трогает).

---

## Чек-лист перед тем, как считать запуск состоявшимся

- [ ] Вход по SSH только по ключу, пароли отключены
- [ ] `ufw status` показывает открытыми только 22, 80, 443
- [ ] `https://домен/api/health` отвечает 200, замок в браузере зелёный
- [ ] Пароль администратора — не `asko2026`
- [ ] `CORS_ORIGINS` содержит боевой адрес фронтенда, без звёздочки
- [ ] Данные перенесены, счётчики сошлись
- [ ] `./scripts/backup.sh` отработал, файлы на месте
- [ ] Восстановление из копии **проверено на деле**
- [ ] Копии уезжают за пределы этого сервера
