#!/usr/bin/env bash
if [[ -n "$DEBUG" ]]; then
  set -x
fi

set -o pipefail  # trace ERR through pipes
set -o errtrace  # trace ERR through 'time command' and other functions
set -o nounset   ## set -u : exit the script if you try to use an uninitialised variable
set -o errexit   ## set -e : exit the script if any statement returns a non-true return value

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )" # http://stackoverflow.com/questions/59895
cd $DIR

usage(){
    echo "psuedo-deploy.sh version-label target=test|prod"
    exit 1
}

if [ $# -ne 2 ];
  then
    usage
fi

source env.$2

ZIP="ucldc-$1.zip"

gulp
# package app and upload
zip $ZIP -r calisphere/ load-content.sh manage.py public_interface/ test/ requirements.txt README.md .ebextensions/ dist/ exhibits/ fixtures/
# copy to s3, create-application-version, update-environment
mkdir ./$1
mv $ZIP ./$1/
cd ./$1/
unzip $ZIP

python manage.py migrate --noinput
python manage.py collectstatic --noinput
python manage.py loaddata fixtures/sites.json
python manage.py runserver
