#!/bin/sh

if [ $# -eq 0 ]
  then
    echo "Le chemin vers le fichier .pgsql est requis."
    exit 1
fi

sudo echo "Recréation et import de la base $DATABASE_URL depuis $DUMP"
read -r -p "Voulez-vous procéder (la base actuelle sera détruite) ? [o/N] " response

case "$response" in
    [oO][eE][sS]|[oO])
        sudo -i -u postgres dropdb access4all
        sudo -i -u postgres createdb access4all
        pg_restore --clean --if-exists --no-owner --no-privileges --dbname $DATABASE_URL $1
        ;;
    *)
        echo "Annulé."
        ;;
esac
