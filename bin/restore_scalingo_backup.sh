#!/usr/bin/env bash
#
# Downloads the latest Scalingo PostgreSQL backup and restores it into the
# local Docker database container.
#
# Containers are stopped (docker compose down) and the pgdata volume is removed
# before restoring, so we start from an empty database. Django migrations are
# then run from the app container.
#
# Requirements: scalingo CLI logged in (scalingo login), docker.
#
# Environment variables (optional overrides):
#   SCALINGO_ADDON      Scalingo addon                   (default: postgres)
#   SCALINGO_REGION     Scalingo region                  (default: osc-fr1)
#   SCALINGO_BACKUP_ID  specific backup id               (default: last successful backup)
#   PG_CONTAINER        local postgres container         (default: access4all_postgresql)
#   KEEP_DUMP=1         keep the dump after restoring
#
# Usage:
#   ./bin/restore_scalingo_backup.sh

set -euo pipefail

SCALINGO_ADDON="${SCALINGO_ADDON:-postgres}"
SCALINGO_REGION="${SCALINGO_REGION:-osc-fr1}"
SCALINGO_BACKUP_ID="${SCALINGO_BACKUP_ID:-}"
PG_CONTAINER="${PG_CONTAINER:-access4all_postgresql}"

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# ./data_psql is mounted on /data_psql in the container (see docker-compose.yml)
HOST_DUMP_DIR="$ROOT_DIR/data_psql"
CONTAINER_DUMP_DIR="/data_psql"

for cmd in scalingo docker tar; do
    command -v "$cmd" > /dev/null || { echo "Commande introuvable : $cmd" >&2; exit 1; }
done

compose() {
    docker compose --project-directory "$ROOT_DIR" -f "$ROOT_DIR/docker-compose.yml" "$@"
}

WORK_DIR="$(mktemp -d "$HOST_DUMP_DIR/restore.XXXXXX")"
cleanup() {
    if [ "${KEEP_DUMP:-0}" != "1" ]; then
        rm -rf "$WORK_DIR"
    else
        echo "Dump conservé dans $WORK_DIR"
    fi
}
trap cleanup EXIT

ARCHIVE="$WORK_DIR/backup.tar.gz"

echo "Téléchargement du backup ${SCALINGO_BACKUP_ID:-le plus récent} (access4all / $SCALINGO_ADDON)..."
scalingo --region "$SCALINGO_REGION" --app access4all --addon "$SCALINGO_ADDON" backups-download \
    ${SCALINGO_BACKUP_ID:+--backup "$SCALINGO_BACKUP_ID"} \
    --output "$ARCHIVE"

echo "Décompression..."
# Scalingo backups are .tar.gz archives containing a .pgsql file; plain .gz is handled too
if tar -tzf "$ARCHIVE" > /dev/null 2>&1; then
    tar -xzf "$ARCHIVE" -C "$WORK_DIR"
else
    gunzip -c "$ARCHIVE" > "$WORK_DIR/backup.pgsql"
fi
rm -f "$ARCHIVE"

DUMP_FILE="$(find "$WORK_DIR" -type f -name '*.pgsql' | head -n 1)"
if [ -z "$DUMP_FILE" ]; then
    echo "Aucun fichier .pgsql trouvé dans l'archive." >&2
    exit 1
fi
CONTAINER_DUMP_FILE="$CONTAINER_DUMP_DIR/${DUMP_FILE#"$HOST_DUMP_DIR"/}"

echo "Dump : $DUMP_FILE"
read -r -p "Les containers vont être arrêtés et la base locale (volume pgdata) supprimée. Continuer ? [o/N] " response
case "$response" in
    [oO]|[oO][uU][iI]) ;;
    *) echo "Annulé."; exit 0 ;;
esac

echo "Arrêt des containers (docker compose down)..."
compose down --remove-orphans

# Only remove the postgres volume (keep the redis one)
PROJECT_NAME="$(compose config --format json | sed -n 's/^ *"name": *"\([^"]*\)".*/\1/p' | head -n 1)"
PGDATA_VOLUMES="$(docker volume ls -q \
    --filter "label=com.docker.compose.project=$PROJECT_NAME" \
    --filter "label=com.docker.compose.volume=pgdata")"
if [ -n "$PGDATA_VOLUMES" ]; then
    echo "Suppression du volume : $PGDATA_VOLUMES"
    # shellcheck disable=SC2086
    docker volume rm $PGDATA_VOLUMES
fi

echo "Démarrage des containers (docker compose up --force-recreate)..."
compose up -d --force-recreate

echo -n "Attente de PostgreSQL"
for _ in $(seq 1 60); do
    # -h localhost: during initialization the temporary server does not listen on TCP
    if docker exec "$PG_CONTAINER" sh -c 'pg_isready -q -h localhost -U "$POSTGRES_USER" -d "$POSTGRES_DB"' 2> /dev/null; then
        echo " OK"
        break
    fi
    echo -n "."
    sleep 2
done
if ! docker exec "$PG_CONTAINER" sh -c 'pg_isready -q -h localhost -U "$POSTGRES_USER" -d "$POSTGRES_DB"' 2> /dev/null; then
    echo
    echo "PostgreSQL ne répond pas dans $PG_CONTAINER." >&2
    exit 1
fi

echo "Restauration (peut prendre plusieurs minutes)..."
# Credentials are read from the container environment (POSTGRES_USER/PASSWORD/DB),
# no secret is stored in this script.
# pg_restore returns a non-zero code on mere warnings (extensions, comments...):
# don't abort the script, just report the exit code.
RESTORE_START=$SECONDS
set +e
docker exec -i "$PG_CONTAINER" sh -c '
    pg_restore --clean --if-exists --no-owner --no-privileges \
        --dbname "postgres://$POSTGRES_USER:$POSTGRES_PASSWORD@localhost/$POSTGRES_DB" \
        "$1"
' sh "$CONTAINER_DUMP_FILE"
status=$?
set -e
RESTORE_DURATION=$((SECONDS - RESTORE_START))

if [ "$status" -ne 0 ]; then
    echo "pg_restore terminé avec des avertissements/erreurs (code $status), vérifier la sortie ci-dessus."
else
    echo "Restauration terminée."
fi
printf "Durée de la restauration : %dmin %02ds\n" $((RESTORE_DURATION / 60)) $((RESTORE_DURATION % 60))

echo "Exécution des migrations (container app)..."
compose exec -T app python manage.py migrate

echo "Terminé."
