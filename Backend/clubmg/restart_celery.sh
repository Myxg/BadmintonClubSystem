#!/bin/bash
source ../py2club/bin/activate
# stop
kill -15 $(cat log/celery.pid)
rm -rf log/celery.pid
sleep 5
# start
celery worker -A clubmg -D -l info --pidfile log/celery.pid -f log/celery.log

