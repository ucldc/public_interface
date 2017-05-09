Docco Documentation
-----------------------------

Docco is listed in devDependences in package.json and should install as part of npm install. Docco converts comments into inline documentation in static HTML pages located in the /docs folder of this repo. Documentation has been checked in to the repo to provide easy timestamping for the last build. 

to build the docs: 

node_modules/docco/bin/docco app/scripts/*.js