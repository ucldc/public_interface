#!/bin/bash

source /var/app/venv/*/bin/activate
echo "starting collect statics";
python manage.py collectstatic --noinput
echo "finished collect statics";
echo $UCLDC_FRONT;
echo "testing access to environment variables inside postdeploy hook";
# echo "finished collect statics, start downloading sitemaps";
# aws s3 cp s3://calisphere-sitemaps/ /var/app/current/sitemaps/ --recursive
# echo "finished downloading sitemaps";
