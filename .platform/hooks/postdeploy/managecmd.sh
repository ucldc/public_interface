#!/bin/bash

source /var/app/venv/*/bin/activate
echo "starting collect statics";
python manage.py collectstatic --noinput
echo "finished collect statis; starting site maps";
python manage.py calisphere_refresh_sitemaps --settings public_interface.settings
echo "finished site maps";

