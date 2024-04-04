#!/bin/bash

source /var/app/venv/*/bin/activate
echo "starting collect statics";
python manage.py collectstatic --noinput
echo "finished collect statics";
