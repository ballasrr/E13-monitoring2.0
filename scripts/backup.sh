#!/bin/sh
# Резервная копия базы и загруженных документов.
#
# Запуск из корня проекта на сервере:
#   ./scripts/backup.sh
# По расписанию (ежедневно в 3:30) — через crontab -e:
#   30 3 * * * cd /opt/e13-monitoring && ./scripts/backup.sh >> /var/log/e13-backup.log 2>&1
#
# Копия, которую ни разу не разворачивали, копией не является.
# Как восстанавливаться — в docs/DEPLOY.md, проверьте это заранее,
# а не в тот день, когда база уже потеряна.
set -eu

COMPOSE="docker compose -f docker-compose.prod.yml"
DEST="${BACKUP_DIR:-/var/backups/e13}"
KEEP_DAYS="${KEEP_DAYS:-14}"
STAMP=$(date +%Y-%m-%d_%H%M)

. ./.env

mkdir -p "$DEST"

echo "[$(date '+%F %T')] резервная копия начата"

# База. Формат custom (-Fc) — сжатый и позволяет восстанавливать
# выборочно, в отличие от простого текстового дампа.
$COMPOSE exec -T db pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc \
	> "$DEST/db-$STAMP.dump"

# Файлы документов лежат в томе Docker, поэтому забираем их изнутри
# контейнера, а не из папки проекта — в проекте их нет.
$COMPOSE exec -T api tar czf - -C /data uploads \
	> "$DEST/uploads-$STAMP.tar.gz"

DB_SIZE=$(du -h "$DEST/db-$STAMP.dump" | cut -f1)
UP_SIZE=$(du -h "$DEST/uploads-$STAMP.tar.gz" | cut -f1)

# Пустой дамп — признак того, что копия не удалась, хотя команда
# завершилась без ошибки. Лучше узнать сейчас, чем при восстановлении.
if [ ! -s "$DEST/db-$STAMP.dump" ]; then
	echo "ОШИБКА: дамп базы пустой" >&2
	exit 1
fi

find "$DEST" -name 'db-*.dump' -mtime +"$KEEP_DAYS" -delete
find "$DEST" -name 'uploads-*.tar.gz' -mtime +"$KEEP_DAYS" -delete

echo "[$(date '+%F %T')] готово: база $DB_SIZE, документы $UP_SIZE, хранить $KEEP_DAYS дней"
