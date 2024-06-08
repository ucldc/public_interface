#!/bin/bash
# NOTE: any changes made to this script should be copied to .platform/hooks/predeploy/managecmd.sh
source /var/app/venv/*/bin/activate

echo "starting collectstatic";
echo "pre-deploy: python manage.py collectstatic --noinput" >> /var/log/collectstatic.log
python manage.py collectstatic --noinput >> /var/log/collectstatic.log 2>&1
echo "finished collectstatic";
