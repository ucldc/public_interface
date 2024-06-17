#!/bin/bash
# NOTE: any changes made to this script should be copied to .platform/hooks/postdeploy/managecmd.sh
source /var/app/venv/*/bin/activate
echo "starting collectstatic";
echo "post-deploy: python manage.py collectstatic --noinput" >> /var/log/collectstatic.log
python manage.py collectstatic --noinput >> /var/log/collectstatic.log 2>&1
echo "finished collectstatic";

echo "start downloading sitemaps";
sitemaps=s3://calisphere-static/sitemaps/
echo "post-deploy: aws s3 cp $sitemaps /var/app/current/sitemaps/ --recursive" >> /var/log/s3_download.log
aws s3 cp s3://calisphere-static/sitemaps/ /var/app/current/sitemaps/ --recursive >> /var/log/s3_download.log 2>&1 || true
echo "finished downloading sitemaps";
