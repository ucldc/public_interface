#!/bin/bash

source /var/app/venv/*/bin/activate
echo "starting collect statics";
ls -la
python manage.py collectstatic --noinput
echo "starting site maps";
python manage.py calisphere_refresh_sitemaps --settings public_interface.settings
la -la static_root
