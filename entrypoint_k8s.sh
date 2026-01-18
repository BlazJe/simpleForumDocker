#!/bin/sh
export DATABASE_URL="mysql+mysqldb://${MYSQL_USER}:${MYSQL_PASSWORD}@${DB_HOST}/${MYSQL_DATABASE}"
echo "Zaganja se aplikacija na hostu $DB_HOST..."
exec "$@"