/*global Backbone, _ */
/*exported FacetFormView */
'use strict';

// Component created if **#js-facet** in DOM    
// templates that include `#js-facet`: `collectionView.html`, `institutionView.html`, `institutionViewItems.html`, `searchResults.html`, `faceting.html`, `paginate.html`

var FacetFormView = Backbone.View.extend({
  el: $('#js-pageContent'),
  
  // User Event Handlers
  // ------------------------------
  // These are event handlers for user interaction with the faceting form, 
  // the search results, and the related collections 
  events: {
    'submit #js-facet'                        : 'setRefineQuery',
    'click .js-refine-filter-pill'            : 'removeRefineQuery',
    'change .js-facet'                        : 'setFacet',
    'click .js-filter-pill'                   : 'removeFacet',
    'click #thumbnails,#list'                 : 'toggleViewFormat',
    'change #pag-dropdown__sort'              : 'setSort',
    'change #pag-dropdown__view'              : 'setRows',
    'click .js-prev,.js-next,a[data-start]'   : 'setStart',
    'change .pag-dropdown__select--unstyled'  : 'setStart',
    'click .js-item-link'                     : 'goToItemPage',
    'click .js-a-check__link-deselect-all'    : 'deselectAll',
    'click .js-a-check__button-deselect-all'  : 'deselectAll',
    'click .js-a-check__link-select-all'      : 'selectAll',
    'click .js-a-check__button-select-all'    : 'selectAll',
    'click .js-clear-filters'                 : 'clearFilters',
    'click .js-a-check__header'               : 'toggleFacetDropdown',
    'click .js-a-check__update'               : 'updateFacets',
    'click .js-rc-page'                       : 'paginateRelatedCollections',
    'click .js-relatedCollection'             : 'goToCollectionPage'
  },

  // **METHODS THAT CHANGE THE QUERY MANAGER**
  
  // These events trigger a change in the model. We don't actually need to submit
  // the form here, because the `FacetFormView` is listening to the model, and
  // whenever the model changes, the `render` method is called

  // `submit` triggered on `#js-facet` (refine button)   
  // the refine button is also the submit button for this form (accessibility requires the form have a submit button)
  setRefineQuery: function(e) {
    this.model.set({start: 0, rq: $.map($('input[name=rq]'), function(el) { return $(el).val(); })});
    e.preventDefault();
  },
  // `click` triggered on `.js-refine-filter-pill` (keyword pills, chiclets)
  removeRefineQuery: function(e) {
    var txtFilter = $(e.currentTarget).data('slug');
    if (_.isNumber(txtFilter)) {
      txtFilter = txtFilter.toString();
    }
    $('input[form="js-facet"][name="rq"][value="' + txtFilter + '"]').val('');
    this.model.set({start: 0, rq: _.without(this.model.get('rq'), txtFilter)});
  },
  // `change` triggered on `.js-facet` (facet checkboxes)
  setFacet: function(e) {
    var filterType = $(e.currentTarget).attr('name');
    var attributes = {start: 0};
    attributes[filterType] = $.map($('input[name=' + filterType + ']:checked'), function(el) { return $(el).val(); });
    this.model.set(attributes);
  },
  // `click` triggered on `.js-filter-pill` (filter pills, chiclets)
  removeFacet: function(e) {
    var filter_slug = $(e.currentTarget).data('slug');
    if (typeof filter_slug !== 'string') {
      filter_slug = String(filter_slug);
    }
    $('#' + filter_slug).prop('checked', false);
    var filterType = $('#' + filter_slug).attr('name');
    var filter = $('#' + filter_slug).attr('value');
    var attributes = {start: 0};
    attributes[filterType] = _.without(this.model.get(filterType), filter);

    this.model.set(attributes);
  },
  // `click` triggered on `#thumbnails,#list` (view format)
  toggleViewFormat: function(e) {
    var viewFormat = $(e.currentTarget).attr('id');
    $('#view_format').prop('value', viewFormat);
    this.model.set({view_format: viewFormat});
  },
  // `change` triggered on `#pag-dropdown__sort`
  setSort: function(e) {
    this.model.set({start: 0, sort: $(e.currentTarget).val() });
  },
  // `change` triggered on `#pag-dropdown__view` (pagination)
  setRows: function(e) {
    this.model.set({start: 0, rows: $(e.currentTarget).val() });
  },
  // `click` triggered on `.js-prev,.js-next,a[data-start]` and
  // `change` triggered on `#pag-dropdown__select--unstyled`
  setStart: function(e) {
    var start;
    if (e.type === 'click') {
      start = $(e.currentTarget).data('start');
    } else if (e.type === 'change') {
      start = $(e.currentTarget).children('option:selected').attr('value');
    }
    $('#start').val(start);
    this.model.set({ start: start });
  },

  // **ITEM QUERY MODEL CHANGES**

  // `click` triggered on `.js-item-link`
  goToItemPage: function(e) {
    // Middle click, cmd click, and ctrl click should open
    // links in a new tab as normal.
    if ( e.which > 1 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey ) { return; }

    // `itemNumber` refers to where the item falls in the current set of search results.
    // This is used in the carousel, because the 6th item in the search results becomes
    // the 1st item in the carousel, but when paginating the carousel, we search for the
    // `itemNumber + <number of carousel thumbs displayed>` - all searches are offest 
    // by the `itemNumber`
    if ($(e.currentTarget).data('item_number') !== undefined) {
      this.model.set({
        itemNumber: $(e.currentTarget).data('item_number'),
        itemId: $(e.currentTarget).data('item_id')
      }, {silent: true});

      // add context for campus, institution, and collection pages
      // for the 'return to' link above the carousel, and for providing
      // context for the carousel search
      if($('#js-institution').length > 0) {
        if($('#js-institution').data('campus')) {
          this.model.set({
            campus_slug: $('#js-institution').data('campus'),
            referral: 'campus',
            referralName: $('#js-institution').data('referralname')
          }, {silent: true});
        } else {
          this.model.set({
            repository_data: $('#js-institution').data('institution'),
            referral: 'institution',
            referralName: $('#js-institution').data('referralname')
          }, {silent: true});
        }
      } else if ($('#js-collection').length > 0) {
        this.model.set({
          collection_data: $('#js-collection').data('collection'),
          referral: 'collection',
          referralName: $('#js-collection').data('referralname')
        }, {silent: true});
      }

      e.preventDefault();
      $.pjax({
        url: $(e.currentTarget).attr('href'),
        container: '#js-pageContent'
      });
    }
  },

  // **BULK QUERY MODEL CHANGES**

  // These functions select or deselect all facets of a given type 
  // (type, decade, collection, institutions)

  // `click` triggered on `.js-a-check__link-deselect-all` and    
  // `click` triggered on `.js-a-check__button-deselect-all`
  deselectAll: function(e) { this.selectDeselectAll(e, false); },
  // `click` triggered on `.js-a-check__link-select-all` and    
  // `click` triggered on `.js-a-check__button-select-all`
  selectAll: function(e) { this.selectDeselectAll(e, true); },
  // helper for `deselectAll` and `selectAll`
  selectDeselectAll: function(e, checked) {
    var filterElements = $(e.currentTarget).parents('.check').find('.js-facet');
    filterElements.prop('checked', checked);
    filterElements.trigger('change');
    e.preventDefault();
  },

  // **CHANGE DISPLAY**
  
  // These methods don't actually change the model, but change the UI and 
  // sometimes manually trigger model changes by calling one of the above methods

  // Helps with the bulk model updater UI. 'Select All' appears as long as
  // fewer than the full set of facets is selected. 'Deselect All' appears
  // *only when all* the facets of that type are selected. 
  toggleSelectDeselectAll: function() {
    var facetTypes = $('.check');
    for(var i=0; i<facetTypes.length; i++) {
      var allSelected = !($($(facetTypes[i]).find('.js-facet')).is(':not(:checked)'));
      if (allSelected === true) {
        // for large screens
        $(facetTypes[i]).find('.js-a-check__link-deselect-all').toggleClass('check__link-deselect-all--not-selected check__link-deselect-all--selected');
        $(facetTypes[i]).find('.js-a-check__link-select-all').toggleClass('check__link-select-all--selected check__link-select-all--not-selected');
        $(facetTypes[i]).find('.js-a-check__button-select-all').prop('disabled', true);
        $(facetTypes[i]).find('.js-a-check__update').prop('disabled', false);
      }
      var oneSelected = $(facetTypes[i]).find('.js-facet').is(':checked');
      if (oneSelected === true) {
        $(facetTypes[i]).find('.js-a-check__button-deselect-all').prop('disabled', false);
      }
    }
  },
  
  // Reset the tooltips
  toggleTooltips: function() {
    // get rid of any visible tooltips
    var visibleTooltips = $('[data-toggle="tooltip"][aria-describedby]');
    for (var i=0; i<visibleTooltips.length; i++) {
      var tooltipId = $(visibleTooltips[i]).attr('aria-describedby');
      $('#' + tooltipId).remove();
    }
    // set tooltips
    $('[data-toggle="tooltip"]').tooltip({
      placement: 'top'
    });
  },

  // `click` triggered on `.js-clear-filters`   
  // programmatically clear all filters, and trigger `change` on `.js-facet` 
  // (model change)
  clearFilters: function() {
    var filterElements = $('.js-facet');
    filterElements.prop('checked', false);
    filterElements.trigger('change');
  },
  
  // **MOBILE EVENT HANDLERS**
  
  // `click` triggered on `.js-a-check__header`   
  // in tablet and mobile, this method opens a list of facets of a given type
  // (no model update)
  toggleFacetDropdown: function(e) {
    //close all expanded checkbox groups
    var allSelected = $('.check__popdown--selected');
    for (var i=0; i<allSelected.length; i++) {
      if ($(allSelected[i]).parent().find('input').attr('name') !== $(e.currentTarget).parent().find('input').attr('name')) {
        $(allSelected[i]).toggleClass('check__popdown check__popdown--selected');
        $(allSelected[i]).prev('.js-a-check__header').children('.js-a-check__header-arrow-icon').toggleClass('fa-angle-down fa-angle-up');
      }
    }
    //open this checkbox group
    $(e.currentTarget).next('.js-a-check__popdown').toggleClass('check__popdown check__popdown--selected');
    $(e.currentTarget).children('.js-a-check__header-arrow-icon').toggleClass('fa-angle-down fa-angle-up');
  },

  // `click` triggered on `.js-a-check__update`   
  // in tablet and mobile, the update button is essentially the same as 
  // kicking off a search
  updateFacets: function(e) {
    e.preventDefault();
    this.facetSearch();
  },
  
  // **PJAX CALL TO PERFORM THE SEARCH** 
  facetSearch: function() {
    $.pjax({
      url: $('#js-facet').attr('action'),
      container: '#js-pageContent',
      data: this.model.toJSON(),
      traditional: true
    });
  },

  // **RELATED COLLECTIONS**

  // These methods deal with the related collections seen below search results

  // `click` triggered on `.js-rc-page`
  paginateRelatedCollections: function(e) {
    // implicitly set institution, campus, and collection data
    if($('#js-institution').length > 0) {
      if($('#js-institution').data('campus')) {
        this.model.set({
          campus_slug: $('#js-institution').data('campus'),
          referral: 'campus',
          referralName: $('#js-institution').data('referralname')
        }, {silent: true});
      } else {
        this.model.set({
          repository_data: $('#js-institution').data('institution'),
          referral: 'institution',
          referralName: $('#js-institution').data('referralname')
        }, {silent: true});
      }
    } else if ($('#js-collection').length > 0) {
      this.model.set({
        collection_data: $('#js-collection').data('collection'),
        referral: 'collection',
        referralName: $('#js-collection').data('referralname')
      }, {silent: true});
    }

    var data_params = this.model.toJSON();
    data_params.rc_page = $(e.currentTarget).data('rc_page');
    // simple AJAX method called here - we don't update the URL
    // as we paginate related collections
    $.ajax({data: data_params, traditional: true, url: '/relatedCollections/', success: function(data) {
        $('#js-relatedCollections').html(data);
      }
    });
  },
  // `click` triggered on `.js-relatedCollection`   
  // when a user navigates away from a search results page to a collection page
  // via related collections, they lose their search context.     
  // this is where it goes.
  goToCollectionPage: function() {
    this.model.clear({silent: true});
  },

  // WINDOW RESIZE TRACKING
  // -----------------------

  // change value of this.desktop to redraw this page when it changes widths
  changeWidth: function(window_width) {
    if (window_width > 900) { this.desktop = true; }
    else { this.desktop = false; }
  },

  // RENDER METHOD
  // ------------------------

  // called whenever the model changes, and also on initialization
  render: function() {
    // if the model has changed, but the primary query hasn't.
    // ie: a search for dogs hasn't become a search for cats
    if(!_.isEmpty(this.model.changed) && !_.has(this.model.changed, 'q')) {
      // if we're in desktop view, just perform the search
      if(this.desktop) {
        this.facetSearch();
      }
      // if we're in mobile view, and a facet selection has changed
      else if(_.has(this.model.changed, 'type_ss') ||
      _.has(this.model.changed, 'facet_decade') ||
      _.has(this.model.changed, 'repository_data') ||
      _.has(this.model.changed, 'collection_data')) {
        var attrUndefined = false;
        _.each(this.model.changed, function(value) {
          if (value === undefined) {
            attrUndefined = true;
          }
        });
        // if the user has un-checked a previously selected facet, perform search
        if (attrUndefined) {
          this.facetSearch();
        }
        // modify the UI
        _.each(this.model.changed, function(value, key) {
          if (key === 'type_ss' || key === 'facet_decade' || key === 'repository_data' || key === 'collection_data') {
            $('.facet-' + key).parents('.check').find('.js-a-check__update').prop('disabled', false);
          }
        });
      } 
      // just perform the search
      else {
        this.facetSearch();
      }
    }
  },

  // PJAX EVENT HANDLERS
  // -----------------------

  // called on `pjax:end`, only when a `FacetFormView` already exists
  // so the user has already visited a search results page
  pjax_end: function(that) {
    return function() {
      // since this is still called on pjax:end when navigating away from 
      // the facet form to something else, we need to check for our
      // `#js-facet` selector
      if ($('#js-facet').length) {
        if (that.popstate === 'back' || that.popstate === 'forward') {
          // when a user navigates 'back' to a form, the form is still set
          // in the state the user left the form in, which doesn't reflect
          // the results shown in search results, so we reset the form
          // to reflect the state the DOM left the form in, last we got a 
          // roundtrip from the server. 
          _.each($('form'), function(form) {
            form.reset();
          });

          // get the query from the DOM, and silently set the model so as 
          // to avoid calling `render` - (no need to redraw the page; the 
          // page has already been drawn)
          var queryObj;
          queryObj = that.model.getQueryFromDOM('js-facet');
          that.model.set(queryObj, {silent: true});
          that.popstate = null;
        }

        // we do need to redraw the tooltips and the select/deselect all 
        // buttons to reflect the current query state, though
        that.toggleSelectDeselectAll();
        that.toggleTooltips();
      }
    };
  },

  pjax_popstate: function(that) {
    return function(e) {
      that.popstate = e.direction;
    };
  },

  // called via `setupComponents()` on `document.ready()` and `pjax:end`
  initialize: function() {
    // sets `this.render` to listen to whenever `this.model` (qm) fires a `change` event
    this.listenTo(this.model, 'change', this.render);
    // draw the page up correctly when initialized
    this.changeWidth($(window).width());
    
    // draw the tooltips and select/deselect all buttons correctly - this
    // happens both on initialization and on pjax:end
    this.toggleSelectDeselectAll();
    this.toggleTooltips();

    // bind pjax handlers to `this`   
    // we need to save the bound handler to `this.bound_pjax_end` so we can 
    // later remove these handlers by the same name in `destroy`
    this.bound_pjax_end = this.pjax_end(this);
    this.bound_pjax_popstate = this.pjax_popstate(this);
    $(document).on('pjax:end', '#js-pageContent', this.bound_pjax_end);
    $(document).on('pjax:popstate', '#js-pageContent', this.bound_pjax_popstate);
  },

  destroy: function() {
    // remove bound pjax event handlers
    $(document).off('pjax:end', '#js-pageContent', this.bound_pjax_end);
    $(document).off('pjax:popstate', '#js-pageContent', this.bound_pjax_popstate);

    // stop calling `this.render` whenever `this.model` (qm) fires a `change` event
    this.stopListening();
    // undelegate all user event handlers specified in `this.events`
    this.undelegateEvents();
  }
});
