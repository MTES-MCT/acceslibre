#!/bin/sh

sudo -u postgres dropdb access4all
sudo -u postgres createdb access4all
pg_restore --clean --if-exists --no-owner --no-privileges \
  --dbname "postgres://access4all:access4all@localhost/access4all" \
  $1

