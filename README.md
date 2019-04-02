# install public interface

To work on this project as a developer, you will actually need to
get python, node, and ruby environments on your development host.

## requirements to build

 * node http://nodejs.org (v10.8) and node's package manager https://npmjs.org
 * requires ruby environment where `gem install sass` has been run
 * requires python environment with `pip` or `virtualenv` set up

### what is happening here?

The root directory of this repository is both the root of a [django applicaiton](https://www.djangoproject.com) and a [Yeoman](http://yeoman.io) scaffold [`yo webapp`](https://github.com/yeoman/generator-webapp#readme) created back when `grunt` was the default task runner.

## configuration 

Based on the advice here here: http://12factor.net/config all configuration is set in environmental variables.

See `env.conf.in` as a tempalte file for setting environmental variables during development.  `env.conf` is listed in `.gitignore` -- so if you use that filename for your local conf, it won't get checked into git.  Before you start the server, you will need to
```
. env.conf
```

If you are working with CDL on developing a feature, contact oacops@cdlib.org for the values to use in the configuration.

## install python / django

python installation left as an exercise to the reader

```
# sudo easy_install virtualenv
virtualenv-2.7 py27
. py27/bin/activate
pip install -r requirements.txt
python manage.py migrate
```

and run the test server

```
python manage.py runserver
```

The Calisphere public interface should be running on http://localhost:8000

## install npm / gulp

if you need to work on the [HTML/CSS/JS](https://github.com/ucldc/public_interface/blob/master/app/ReadMe.md) then you will want to run gulp to assemble these components.

```
brew install npm
npm install -g gulp-cli
npm install
```

```
gulp serve
```

An html/design reference site will be running on http://localhost:9000/ 

# windows install

[note, use case for windows users is for QA of candiate producton indexes, not code hacking]

http://conda.pydata.org/miniconda.html  <-- python 2.7

http://git-scm.com/download/win

save `run.bat`

## initial setup
only do this once
```dos
conda create -n myenv python
activate myenv
git clone https://github.com/ucldc/public_interface.git
cd public_interface
pip install -r requirements.txt
```
edit `run.bat` in notepad, as per below
```
run.bat
```

## run again

```dos
activate myenv
cd public_interface
```
if you need to update the code

```
git pull origin master
```
run the local server on http://localhost:8000/
```
run.bat
```

## `run.bat`:
```bat
set UCLDC_THUMBNAIL_URL=...
set UCLDC_STATIC_URL=...
set UCLDC_SOLR_URL=...
set UCLDC_SOLR_API_KEY=...
set UCLDC_DEBUG=1
set UCLDC_IMAGES=...
set UCLDC_MEDIA=...
set UCLDC_IIIF=...
python manage.py runserver
```

# Deploy to Amazon Web Services Elastic Beanstalk
Run within an authorized shell (on an EC2 instance with IAM permissions)

```
deploy-version.sh
```
will show the running environments and the last few version names.  Then run

```
deploy-version.sh version-label environment-name
```

# Generate Static Sitemaps
To generate or update sitemaps, first make sure that "UCLDC_FRONT" has been defined in your `env.local` file. For example:

```
UCLDC_FRONT="https://calisphere.org/"
```

Also make sure that the `domain` is set correctly using the django ["sites" framework](https://docs.djangoproject.com/en/1.10/ref/contrib/sites/)
 
Then, run:

```
python manage.py calisphere_refresh_sitemaps
```
For more verbose output, use the `-v` option (1-3, with 3 being the most verbose).

This will generate sitemap files and write them to the `sitemaps` directory in the root of the Django instance. 

The sitemap.xml index file will be served statically by Django at the `UCLDC_FRONT` URL, i.e. https://calisphere.org/sitemap.xml

Right now, each `sitemap-items-*.xml` file contains 50,000 urls and is under 10MB uncompressed, which is the [google limit](https://support.google.com/webmasters/answer/183668?hl=en&ref_topic=4581190). Some are over 9MB in size though, so if we add more metadata in the future, we might need to reduce the number of urls per file.

# Testing via Backstop.js

For now, make sure to install backstop globally, add to your PATH, or modify the commands below to include the path (node_modules/.bin/backstop), then run: 

Testing production vs. calisphere-test 
```
backstop reference --config backstop_data/backstop_tests/prod-vs-test-ui.js
backstop test --config backstop_data/backstop_tests/prod-vs-test-ui.js

backstop reference --config backstop_data/backstop_tests/prod-vs-test-app.js
backstop test --config backstop_data/backstop_tests/prod-vs-test-app.js
```

Testing production vs. localhost:9000 for the UI library and vs. 127.0.0.1:8000 for the app
(must `gulp serve` and `python manage.py runserver` before running these tests)
```
backstop reference --config backstop_data/backstop_tests/prod-vs-local-ui.js
backstop test --config backstop_data/backstop_tests/prod-vs-local-ui.js

backstop reference --config backstop_data/backstop_tests/test-vs-local-ui.js
backstop test --config backstop_data/backstop_tests/test-vs-local-ui.js
```

Testing calisphere-test vs. localhost:9000 for the UI library and vs. 127.0.0.1:8000 for the app
(must `gulp serve` and `python manage.py runserver` before running these tests)
```
backstop reference --config backstop_data/backstop_tests/prod-vs-local-app.js
backstop test --config backstop_data/backstop_tests/prod-vs-local-app.js

backstop reference --config backstop_data/backstop_tests/test-vs-local-app.js
backstop test --config backstop_data/backstop_tests/test-vs-local-app.js
```

Hope to incorporate into build tools at some point in the future. 