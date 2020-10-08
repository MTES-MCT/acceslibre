#!/bin/sh

DUMP_PATH="/tmp/dump.pgsql"

# TODO check if scalingo cli is available
SCALINGO_POSTGRESQL_URL=`scalingo env | grep 'postgres://' | awk -F '=' '{ print $2 }'`
PARTS=$(echo "$SCALINGO_POSTGRESQL_URL" | grep -oP '\w+')
USERNAME=$(echo $PARTS | awk '{ print $2 }')
PASSWORD=$(echo $PARTS | awk '{ print $3 }')
DATABASE=$USERNAME
TUNNEL_DB_URL="postgresql://$USERNAME:$PASSWORD@127.0.0.1:10000/$USERNAME"

echo "Opening tunnel at $TUNNEL_DB_URL"
scalingo db-tunnel SCALINGO_POSTGRESQL_URL &
tunnel_pid=$!
sleep 2
echo "Tunnel started with pid $tunnel_pid"

echo "Dumping db to $DUMP_PATH"
echo "WARNING: this could take several minutes, just be patient."
pg_dump --clean --if-exists --format c --dbname "$TUNNEL_DB_URL" --no-owner --no-privileges --exclude-schema 'information_schema' --exclude-schema '^pg_*' --file $DUMP_PATH

echo "Restoring locally to $DATABASE_URL"
pg_restore --clean --if-exists --no-owner --no-privileges --dbname "$DATABASE_URL" /tmp/dump.pgsql

echo "Closing tunnel"
kill -TERM "${tunnel_pid}" > /dev/null 2>&1

echo "Done."
