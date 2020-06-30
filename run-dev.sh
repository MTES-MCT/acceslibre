#!/usr/bin/env bash

# Run Django dev server along sass watch daemon in parallel, handling
# ctrl-c termination. Inspired by https://unix.stackexchange.com/a/478574.

SOURCE_SCSS="static/scss/style.scss"
TARGET_CSS="static/css/style.css"

function ctrl_c() {
  echo "Shutting down development servers"
  kill -TERM "${runserver_pid}" > /dev/null 2>&1
  kill -TERM "${sasswatch_pid}" > /dev/null 2>&1
  echo "OK"
  exit 0
}

trap ctrl_c INT

python manage.py runserver --insecure &
runserver_pid=$!
python manage.py sass $SOURCE_SCSS $TARGET_CSS --watch -t compressed &
sasswatch_pid=$!

wait ${runserver_pid} > /dev/null 2>&1
wait ${sasswatch_pid} > /dev/null 2>&1
trap - INT
