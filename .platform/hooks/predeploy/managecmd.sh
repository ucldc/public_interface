#!/bin/bash
# NOTE: any changes made to this script should be copied to .platform/confighooks/predeploy/managecmd.sh
source /var/app/venv/*/bin/activate

filename="${UCLDC_REDIRECT_IDS##*/}"
echo "start downloading redirects from $UCLDC_REDIRECT_IDS to $(pwd)/$filename";
echo "pre-deploy: aws s3 cp $UCLDC_REDIRECT_IDS . " >> /var/log/s3_download.log
aws s3 cp $UCLDC_REDIRECT_IDS . >> /var/log/s3_download.log 2>&1

echo "download complete; creating redirect map";
httxt2dbm -i $filename -o CSPHERE_IDS.map
mv CSPHERE_IDS.map /var/app/

echo "create off-site redirect map";
httxt2dbm -i off_csphere.txt -o OFF_CSPHERE.map
mv OFF_CSPHERE.map /var/app/