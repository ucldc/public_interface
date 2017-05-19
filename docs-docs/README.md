Docco Documentation
-----------------------------

Docco is listed in `devDependences` in `package.json` and should install as part of `npm install`. Docco converts comments into inline documentation in static HTML pages located in the `/docs` folder of this repo. Documentation has been checked in to the repo to provide easy timestamping for the last build of the docs.

To build the docs run: 

```
node_modules/docco/bin/docco app/scripts/*.js
```

JavaScript Overview
------------------------------

Generally, templating and data marshalling happens server side in Django templates and views, respectively. The templates are served to the client as either a page, an AJAX response, or a PJAX response. The JavaScript then resolves its state with the server's response - hence the `QueryManager`'s `getQueryFromDOM` and `getItemInfoFromDOM` functions. 

Scripts are loaded in the following order (from `/calisphere/templates/calisphere/scripts.html` for devMode and `/app/index.html` for production)

`/calisphere/templates/calisphere/scripts.html`
```
  <script src="{% static "scripts/Controller.js" %}"></script>
  <script src="{% static "scripts/QueryManager.js" %}"></script>
  <script src="{% static "scripts/ExhibitPageView.js" %}"></script>
  <script src="{% static "scripts/FacetFormView.js" %}"></script>
  <script src="{% static "scripts/ItemView.js" %}"></script>
  <script src="{% static "scripts/ComplexCarouselView.js" %}"></script>
  <script src="{% static "scripts/GlobalSearchFormView.js" %}"></script>
  <script src="{% static "scripts/ContactOwnerFormView.js" %}"></script>
  ...
  <script src="{% static "scripts/calisphere.js" %}"></script>
```

`/app/index.html`
```
  <!-- build:js(app) scripts/calisphere.js -->
  <script src="scripts/Controller.js"></script>
  <script src="scripts/QueryManager.js"></script>
  <script src="scripts/ExhibitPageView.js"></script>
  <script src="scripts/FacetFormView.js"></script>
  <script src="scripts/ItemView.js"></script>
  <script src="scripts/ComplexCarouselView.js"></script>
  <script src="scripts/GlobalSearchFormView.js"></script>
  <script src="scripts/ContactOwnerFormView.js"></script>
  <script src="scripts/calisphere.js"></script>
  <!-- endbuild -->



  <!-- build:js scripts/calisphere-home.js -->
  <script src="scripts/calisphere-home.js"></script>
  <!-- endbuild -->
```

`calisphere.js` is the last loaded file and kicks everything else off - start here to follow what happens when a page is loaded. `calisphere.js` creates `qm`, the globally namespaced `QueryManager`, as well as the globally namespaced `globalSearchForm`, and then uses the `setupComponents` function in `Controller.js` to determine which components to create/destroy based on which selectors are available in the DOM. 

The homepage is the one place where `calisphere.js` is **not** used. For the homepage, the only JavaScript loaded is in `calisphere-home.js`

For more information on the JavaScript, clone this repo locally, and open the `index.html` file in this directory. 
