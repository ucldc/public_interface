// can only run after 'gulp serve'
require("./backstop_data/ui-library-backstop-scenarios.js")({
      "urlRoot": "http://localhost:9000",
      "referenceUrlRoot": "http://calisphere-test.cdlib.org/static_root"
    }),
// can only run after gulp serve AND python manage.py runserver
require("./backstop_data/calisphere-backstop-scenarios.js")({
      "urlRoot": "http://127.0.0.1:8000",
      "referenceUrlRoot": "http://calisphere-test.cdlib.org"
    }),

// can run whenever! 
require("./backstop_data/ui-library-backstop-scenarios.js")({
      "urlRoot": "http://calisphere-test.cdlib.org/static_root",
      "referenceUrlRoot": "https://calisphere.org/static_root"
    }),
require("./backstop_data/calisphere-backstop-scenarios.js")({
      "urlRoot": "http://calisphere-test.cdlib.org",
      "referenceUrlRoot": "https://calisphere.org"
    }),
// 
// ==================================================================
// second tactic: remove KievitWeb from calisphere-test and calisphere-prod
// 
// run whenever, set UCLDC_STATIC_TEST to either http://localhost:9000 after 'gulp serve'
// or set to http://calisphere-test.cdlib.org/static_root as part of deploy-version.sh?
require("./backstop_data/ui-library-backstop-scenarios.js")({
      "urlRoot": "http://localhost:9000",
    }),
// run whenever, set UCLDC_TEST to either http://127.0.0.1:8000 after python manage.py runserver
// or set to http://calisphere-test.cdlib.org as part of deploy-version.sh?
require("./backstop_data/calisphere-backstop-scenarios.js")({
      "urlRoot": "http://127.0.0.1:8000",
    }),
