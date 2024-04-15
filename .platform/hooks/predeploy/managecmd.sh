#!/bin/bash

source /var/app/venv/*/bin/activate

echo "starting collect statics";
python manage.py collectstatic --noinput
echo "finished collect statics";

filename="${UCLDC_REDIRECT_IDS##*/}"
echo "start downloading redirects from $UCLDC_REDIRECT_IDS to $(pwd)/$filename";
aws s3 cp $UCLDC_REDIRECT_IDS .

echo "download complete; creating redirect map";
httxt2dbm -i $filename -o CSPHERE_IDS.map
mv CSPHERE_IDS.map /var/app/

echo "TODO: still need to create off-site redirect map OFF_CSPHERE.map"

# echo "start creating off-site redirects";
# httxt2dbm -i $filename -o OFF_CSPHERE.map
# aws s3 cp s3://static-ucldc-cdlib-org/redirects/CSPHERE_IDS-2023-11-03.txt /var/app/current/redirects/ --recursive || true