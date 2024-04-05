#!/bin/bash

source /var/app/venv/*/bin/activate
echo "starting collect statics";
python manage.py collectstatic --noinput
echo "finished collect statics";
echo "start downloading sitemaps";
aws s3 cp s3://static-ucldc-cdlib-org/sitemaps/2024-04-03-calisphere-prd/ /var/app/current/sitemaps/ --recursive || true
echo "finished downloading sitemaps";
