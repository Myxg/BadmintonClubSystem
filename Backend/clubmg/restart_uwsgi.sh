#!/bin/bash

workdir=$(cd $(dirname $0); pwd)

source ../py2club/bin/activate

uwsgi --stop log/uwsgi.pid
sleep 2
uwsgi --ini uwsgi.ini

