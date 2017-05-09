Docco Documentation
-----------------------------

Docco is listed in `devDependences` in `package.json` and should install as part of `npm install`. Docco converts comments into inline documentation in static HTML pages located in the `/docs` folder of this repo. Documentation has been checked in to the repo to provide easy timestamping for the last build of the docs.

To build the docs run: 

```
node_modules/docco/bin/docco app/scripts/*.js
```

Documentation Overview
------------------------------

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

[`calisphere.js`](amywieliczka.github.io/calisphere.html ) is the last loaded file and kicks everything else off - start here to follow what happens when a page is loaded. `calisphere.js` creates `qm`, the globally namespaced [`QueryManager`](amywieliczka.github.io/QueryManager.html), as well as the globally namespaced [`globalSearchForm`](amywieliczka.github.io/GlobalSearchFormView.html), and then uses the `setupComponents` function in [`Controller.js`](amywieliczka.github.io/Controller.html) to determine which components to create/destroy based on which selectors are available in the DOM. 

The homepage is the one place where `calisphere.js` is **not** used. For the homepage, the only JavaScript loaded is in [`calisphere-home.js`](amywieliczka.github.io/calisphere-home.html). 

A bit about namespacing
----------------------------

All components are created as subcomponents of the `globalSearchForm`. This means, at any given point in time, you can type `globalSearchForm` into the console and components should exist as properties of the `globalSearchForm` (see list below). Likewise, `qm` is available in the global namespace. Typing `qm.attributes` into the JavaScript console will print the current query state, and should always match `sessionStorage`. 

Calisphere Components:
* if `#js-facet` selector in DOM, create a [`FacetFormView`](amywieliczka.github.io/FacetFormView.html) attached to `globalSearchForm` at `globalSearchForm.facetForm`
* if `#js-carouselContainer` selector in DOM, create a [`ItemView`](amywieliczka.github.io/ItemView.html) attached to `globalSearchForm` at `globalSearchForm.carousel`
* if `#js-contactOwner` selector in DOM, create a [`ContactOwnerFormView`](amywieliczka.github.io/ContactOwnerFormView.html) attached to `globalSearchForm` at `globalSearchForm.contactOwnerForm`
* if `.carousel-complex` selector in DOM, create a [`ComplexCarouselView`](amywieliczka.github.io/ComplexCarouselView.html) attached to `globalSearchForm` at `globalSearchForm.complexCarousel`
* if `#js-exhibit-title` selector in DOM, create a [`ExhibitPageView`](amywieliczka.github.io/ExhibitPageView.html) attached to `globalSearchForm` at `globalSearchForm.exhibitPage`

Calisphere Components
----------------------------

Calisphere components extend the [Backbone.js View class](http://backbonejs.org/#View) while the `QueryManager` extends the [Backbone.js Model class](http://backbonejs.org/#Model). Check out http://backbonejs.org/#Model-View-separation for an introduction to how Backbone Models and Views are related. 

Calisphere components tend to have a few distinct flavors of methods:
* User-Interaction Event Handlers (specified in the `events` dictionary and attached by default on component creation)
* PJAX Event Handlers (always defined in the form `pjax_<pjax event name>` and bound in a component's `initialize` function)
* Window resize event handler (always called `changeWidth`. The `GlobalSearchFormView.changeWidth(<window width>)` calls each component's changeWidth function. `globalSearchForm.changeWidth` is called in `calisphere.js`.)
* Lifecycle methods: `initialize`, `render`, and `destroy`. 

**Component Lifecycle**

- Initialize (required)
If a component's `render` method is defined, `initialize` will always instruct the component to `listenTo` a `change` on the component's `model` (in our case, always `qm`) and call the component's `render` method.
If a component's `changeWidth` method is defined, `initialize` will always call the `changeWidth` function to ensure the component is drawn up correctly on initialization. 
Finally, all PJAX event handlers must be attached (`.on`) by a persistent name in `initialize`. 

- Render (optional)
If a component defines a `render` method, this is the method called on the view when the query state changes. 

- Destroy (required)
All PJAX event handlers must be detached (`.off`) by a persistent name in `destroy`. 
If a component has been instructed to `listenTo` changes in the component's model in `initialize` then the component must `stopListening` in `destroy`.
`this.undelegateEvents()` must be called to detach user-interaction events specified in the `events` dictionary of a component. 

Creating a New Component
-------------------------------
