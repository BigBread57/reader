#!/bin/bash
set -e

if [ -n "$DB_NAME" ]; then
	echo "Creating database: $DB_NAME"

	psql=( psql -v ON_ERROR_STOP=1 )

    "${psql[@]}" --username $DB_USER <<-EOSQL
        CREATE DATABASE "$DB_NAME" TEMPLATE template1;
EOSQL

    if [ -f /backup/base.dump ]; then
        echo "DUMP!!!!"
        pg_restore --username $POSTGRES_USER --no-owner -d $POSTGRES_DB /backup/base.dump
    fi
fi