#!/bin/sh

# Preberi geslo za bazo iz secreta
if [ -f /run/secrets/db_password ]; then
    export DB_PASSWORD=$(cat /run/secrets/db_password)
fi

# Preberi secret key
if [ -f /run/secrets/flask_secret ]; then
    export SECRET_KEY=$(cat /run/secrets/flask_secret)
fi

# MySQL connection string za SQLAlchemy
# Format: mysql+mysqldb://user:password@host/dbname
export DATABASE_URL="mysql+mysqldb://flask_user:$DB_PASSWORD@db/flaskdb"

echo "Zaganja se aplikacija... Povezujem se na bazo..."

# Poženi ukaz (gunicorn)
exec "$@"