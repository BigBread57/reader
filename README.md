# Команда для загрузки БД из dump
pg_restore --username $POSTGRES_USER --no-owner -c -d $POSTGRES_DB /backup/base.dump