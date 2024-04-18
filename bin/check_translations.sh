#!/usr/bin/env bash

set -e # exit if any command has a non-zero exit status
set -u # consider unset variables as errors
set -o pipefail # prevents errors in a pipeline from being masked

RETURN=0

for LOCAL_DIR in locale/*; do
    cp $LOCAL_DIR/LC_MESSAGES/django.po $LOCAL_DIR/LC_MESSAGES/django.po.original
    cp $LOCAL_DIR/LC_MESSAGES/djangojs.po $LOCAL_DIR/LC_MESSAGES/djangojs.po.original

    pipenv run make messages

    diff $LOCAL_DIR/LC_MESSAGES/django.po $LOCAL_DIR/LC_MESSAGES/django.po.original || { RETURN=$?; echo "make messages generates extra diff, maybe you should run make messages and commit the change";}
    diff $LOCAL_DIR/LC_MESSAGES/djangojs.po $LOCAL_DIR/LC_MESSAGES/djangojs.po.original || { RETURN=$?; echo "make messages generates extra diff, maybe you should run make messages and commit the change";}

    set +e
    grep_fuzzy=$(grep -En "^#(, .*)?, fuzzy(, .*)?$"  $LOCAL_DIR/LC_MESSAGES/django.po)
    set -e
    if [[ "$grep_fuzzy" ]]
    then
      RETURN=1
      echo ".po file contains fuzzy messages:"
      echo "$grep_fuzzy"
    fi
done

exit $RETURN
