#!/bin/bash

source /var/app/venv/*/bin/activate

filename="${UCLDC_REDIRECT_IDS##*/}"
echo "start downloading redirects from $UCLDC_REDIRECT_IDS to $(pwd)/$filename";
echo "pre-deploy: aws s3 cp $UCLDC_REDIRECT_IDS . " >> /var/log/s3_download.log
aws s3 cp $UCLDC_REDIRECT_IDS . >> /var/log/s3_download.log 2>&1

echo "download complete; creating redirect map";
httxt2dbm -i $filename -o CSPHERE_IDS.map
mv CSPHERE_IDS.map /var/app/

echo "TODO: still need to create off-site redirect map OFF_CSPHERE.map"
