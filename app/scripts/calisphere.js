/* global QueryManager, GlobalSearchFormView, setupComponents, clusters */
/* exported get_cali_ga_dimensions, get_inst_ga_dimensions */

/* globals Modernizr: false */
'use strict';

// Cope with browser variance
// --------------------------

// Called on document ready, adds banner notice
// to DOM for users without session storage
function sessionStorageWarning() {
  if (! Modernizr.sessionstorage) {
    $('body').prepend(
      $('<div/>', {'class': 'container-fluid'})
      .append(
        $('<div/>', {
          'class': 'alert alert-warning alert-dismissible',
          'role': 'alert'
        }).text('Some features on the Calisphere beta site do not yet work in private browsing mode. For an optimal experience, please disable private browsing while on this site.')
        .append('<button type="button" class="close" data-dismiss="alert" aria-label="Close"><span aria-hidden="true">&times;</span></button>')
      )
    );
  }
}

// For IE
if(typeof console === 'undefined') {
  console = { log: function() { } };
}

var qm, globalSearchForm;

function timeoutGACallback(callback, opt_timeout) {
  var called = false;
  function fn(){
    if (!called) {
      called = true;
      callback();
    }
  }
  setTimeout(fn, opt_timeout || 1000);
  return fn;
}

function get_cali_ga_dimensions() {
  var dim1 = $('[data-ga-dim1]').data('ga-dim1');
  var dim2 = $('[data-ga-dim2]').data('ga-dim2');
  var dim3 = Modernizr.sessionstorage.toString();
  var dim4 = $('[data-ga-dim4]').data('ga-dim4');
  var dimensions = {};
  if (dim1) { dimensions.dimension1 = dim1; }
  if (dim2) { dimensions.dimension2 = dim2; }
  if (dim3) { dimensions.dimension3 = dim3; }
  if (dim4) { dimensions.dimension4 = dim4; }

  return dimensions;
}

function get_inst_ga_dimensions() {
  var dim1 = $('[data-ga-dim1]').data('ga-dim1');
  var dim2 = $('[data-ga-dim2]').data('ga-dim2');
  var dimensions = {};
  if (dim1) { dimensions.dimension1 = dim1; }
  if (dim2) { dimensions.dimension2 = dim2; }

  return dimensions;
}

// Initial Setup for all Calisphere pages
// ----------------

$(document).ready(function() {
  // ***********************************
  on_ready_handler();

  // **Google Event Tracking**

  // based on https://support.google.com/analytics/answer/1136920?hl=en
  // We capture the click handler on outbound links and the contact owner button

  var outboundSelector = 'a[href^="http://"], a[href^="https://"]';
  outboundSelector += ', button[onclick^="location.href\=\'http\:\/\/"]';
  outboundSelector += ', button[onclick^="location.href\=\'https\:\/\/"]';

  if (typeof ga !== 'undefined') {
    $('body').on('click', outboundSelector, function() {
      var url = '';
      if($(this).attr('href')) {
        url = $(this).attr('href');
      } else if($(this).attr('onclick')) {
        var c = $(this).attr('onclick');
        url = c.slice(15, c.length-2);
      }

      var fieldsObject = get_cali_ga_dimensions();
      fieldsObject.transport = 'beacon'; // use navigator.sendBeacon
      fieldsObject.hitCallback = timeoutGACallback(function(){
        // click captured and tracked, send the user along
        document.location = url;
      });
      ga('caliga.send', 'event', 'outbound', 'click', url, fieldsObject);
      return false;
    });

    $('.button__contact-owner').on('click', function() {
      var url = $(this).attr('href');

      var fieldsObject = get_cali_ga_dimensions();
      fieldsObject.transport = 'beacon'; // use navigator.sendBeacon
      fieldsObject.hitCallback = timeoutGACallback(function() {
        document.location = url;
      });
      ga('caliga.send', 'event', 'buttons', 'contact', url, fieldsObject);
      return false;
    });
  }
  if (typeof _paq !== 'undefined' ) {
    $('body').on('click', outboundSelector, function() {
      var url = '';
      if($(this).attr('href')) {
        url = $(this).attr('href');
      } else if($(this).attr('onclick')) {
        var c = $(this).attr('onclick');
        url = c.slice(15, c.length-2);
      }

      // https://developer.matomo.org/guides/tracking-javascript-guide#tracking-a-custom-dimension-for-one-specific-action-only
      _paq.push(['trackEvent', 'outbound', 'click', url,
        undefined, get_cali_ga_dimensions(), 
        timeoutGACallback(function(){
          // click captured and tracked, send the user along
          document.location = url;
        })]);
      return false;
    });

    $('.button__contact-owner').on('click', function() {
      var url = $(this).attr('href');

      _paq.push(['trackEvent', 'buttons', 'contact', url,
        undefined, get_cali_ga_dimensions(), 
        timeoutGACallback(function() {
          document.location = url;
        })]);
      return false;
    });
  }
  // ***********************************

  // Add banner notice for users without session storage
  sessionStorageWarning();
  // ***********************************

  // **Window Resize Tracking**

  // based on http://stackoverflow.com/questions/5489946/jquery-how-to-wait-for-the-end-of-resize-event-and-only-then-perform-an-ac
  // We redraw the page at the end of a resize event if the window
  // has fallen below or above a particular breakpoint.
  // This ensures we only redraw the page once, when the user
  // has stopped resizing the window.
  var rtime;
  var timeout = false;
  var delta = 200;
  $(window).resize(function() {
      rtime = new Date();
      if (timeout === false) {
          timeout = true;
          setTimeout(resizeend, delta);
      }
  });

  function resizeend() {
      if (new Date() - rtime < delta) {
          setTimeout(resizeend, delta);
      } else {
          timeout = false;
          if (globalSearchForm) {
            globalSearchForm.changeWidth($(window).width());
          }
      }
  }
  // ***********************************

  // **Initial Setup for all Calisphere pages except the homepage**

  // The homepage doesn't have JS components to initialize
  if (!$('.home').length) {

    // **Initial Component Setup**

    //Create query manager and global search form component
    qm = new QueryManager();
    globalSearchForm = new GlobalSearchFormView({model: qm});

    //`setupComponents()` acts as a controller to create/destroy JS components
    //based on which selectors are available/no longer available in the DOM.
    setupComponents(globalSearchForm, qm);
  }
});

var cluster_search = function(col_id, facet_field) {
  var clusterSearch = new Bloodhound({
      datumTokenizer: Bloodhound.tokenizers.obj.whitespace('label'),
      queryTokenizer: Bloodhound.tokenizers.whitespace,
      prefetch: '/collections/' + col_id + '/' + facet_field + '.json'
  });
  $('#clustersearch__field-' + facet_field).typeahead(null, {
    name: facet_field + 'Clusters',
    display: 'label',
    limit: 10,
    source: clusterSearch
  }).on('keydown', function(event) {
    var x = event.which;
    if (x === 13) {
      event.preventDefault();
    }
  }).bind('typeahead:selected', function(obj, datum) {
    window.location = datum.uri;
  });
};

var on_ready_handler = function() {
  // send google analytics on pjax pages 
  /* globals ga: false, _paq: false */
  /* jshint latedef: false */
  // if (typeof _paq !== 'undefined') {
  //   _paq.push(['setCustomUrl', window.location.href]);
  //   _paq.push(['setDocumentTitle', document.title]);
  //   _paq.push(['trackPageView', document.title, get_cali_ga_dimensions()]);
  //   _paq.push(['enableLinkTracking']);
  // }
  // if (typeof ga !== 'undefined') {
  //   var dimensions = get_cali_ga_dimensions();
  //   ga('caliga.set', 'location', window.location.href);
  //   ga('caliga.send', 'pageview', dimensions);

  //   var inst_ga_code = $('[data-ga-code]').data('ga-code');
  //   if (inst_ga_code) {
  //     var inst_tracker_name = inst_ga_code.replace(/-/g,'x');
  //     ga('create', inst_ga_code, 'auto', {'name': inst_tracker_name});
  //     ga(inst_tracker_name + '.set', 'anonymizeIp', true);
  //     ga(inst_tracker_name + '.set', 'location', window.location.href);
  //     var inst_dimensions = get_inst_ga_dimensions();
  //     ga( inst_tracker_name + '.send', 'pageview', inst_dimensions);
  //   }
  // }

  // **Collection Title Search**

  /* globals Bloodhound: false */
  if ($('#titlesearch__field').length) {
    var collections = new Bloodhound({
      datumTokenizer: Bloodhound.tokenizers.obj.whitespace('title'),
      queryTokenizer: Bloodhound.tokenizers.whitespace,
      prefetch: '/collections/titles.json'
    });
    // chain things to the titlesearch field
    $('#titlesearch__field').typeahead(null, {
      name: 'collections',
      display: 'title',
      limit: 10,
      source: collections
    }).on('keydown', function(event) {
      // disable enter
      // http://stackoverflow.com/a/21318996/1763984
      var x = event.which;
      if (x === 13) {
       event.preventDefault();
      }
    }).bind('typeahead:selected', function(obj, datum) {
      // redirect to the select page
      window.location = datum.uri;
    });
  } // end title search

  if ($('.cluster-listing').length) {
    for (var i=0; i<clusters.clusters.length; i++) {
      cluster_search(clusters.collection_id, clusters.clusters[i]);
    }
  }

  if ($('#js-collectionFacetForm').length) {
    $('.js-view_format-toggle').click(function(e) {
      e.preventDefault();
      if ($(e.currentTarget).attr('id') === 'list') {
        $('input[name=view_format]').val('list');
      } else if ($(e.currentTarget).attr('id') === 'grid') {
        $('input[name=view_format]').val('grid');
      }
      $('#js-collectionFacetForm').submit();
    });

    $('#js-sort-selector').change(function() {
      $('#js-collectionFacetForm').submit();
    });
  }
};

//************************************

// No support for background-blend-mode
if(!('backgroundBlendMode' in document.body.style)) {
  var html = document.getElementsByTagName('html')[0];
  html.className = html.className + ' no-background-blend-mode';
}
