/* global QueryManager, GlobalSearchFormView, setupComponents */

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

// PJAX explained more a bit later, for now this is just a timeout
$(document).on('pjax:timeout', function() { return false; });

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

// Initial Setup for all Calisphere pages
// ----------------

$(document).ready(function() {
  // ***********************************
  on_ready_pjax_end_handler()

  // **Google Event Tracking**

  // based on https://support.google.com/analytics/answer/1136920?hl=en
  // We capture the click handler on outbound links and the contact owner button

  if (typeof ga !== 'undefined') {
    var outboundSelector = 'a[href^="http://"], a[href^="https://"]';
    outboundSelector += ', button[onclick^="location.href\=\'http\:\/\/"]';
    outboundSelector += ', button[onclick^="location.href\=\'https\:\/\/"]';
    $('body').on('click', outboundSelector, function() {
      var url = '';
      if($(this).attr('href')) {
        url = $(this).attr('href');
      } else if($(this).attr('onclick')) {
        var c = $(this).attr('onclick');
        url = c.slice(15, c.length-2);
      }

      ga('send', 'event', 'outbound', 'click', url, {
        'transport': 'beacon',  // use navigator.sendBeacon
        // click captured and tracked, send the user along
        'hitCallback': timeoutGACallback(function() {
          document.location = url;
        })
      });
      return false;
    });

    $('.button__contact-owner').on('click', function() {
      var url = $(this).attr('href');
      ga('send', 'event', 'buttons', 'contact', url, {
        'transport': 'beacon',  // use navigator.sendBeacon
        'hitCallback': timeoutGACallback(function () {
          document.location = url;
        })
      });
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

  // The homepage doesn't have pjax-y links, or JS components to initialize
  if (!$('.home').length) {

    // **PJAX**

    // We use pjax (pushState+ajax) to replace the inner HTML of given DOM 
    // nodes (typically `#js-pageContent`), and update the address bar accordingly.
    // https://github.com/defunkt/jquery-pjax
    $.pjax.defaults.timeout = 5000;
    // make all links with attribute `data-pjax=js-PageContent` pjax-y
    $(document).pjax('a[data-pjax=js-pageContent]', '#js-pageContent');

    // **Initial Component Setup**

    //Create query manager and global search form component
    qm = new QueryManager();
    globalSearchForm = new GlobalSearchFormView({model: qm});

    //`setupComponents()` acts as a controller to create/destroy JS components
    //based on which selectors are available/no longer available in the DOM.
    setupComponents(globalSearchForm, qm);

    // **Global PJAX Event Handlers**

    // https://github.com/defunkt/jquery-pjax#events
    
    //**Pjax Success**
    $(document).on('pjax:success', function(e, data, x, xhr, z) {
      var start_marker = z.context.find('meta[property=og\\:type]');
      var variable_markup = start_marker.nextUntil($('meta[name=twitter\\:creator]'));
      var old_start = $('head').find('meta[property=og\\:type]');
      old_start.nextUntil($('meta[name=twitter\\:creator]')).remove();
      $.each($(variable_markup).get().reverse(), function(i, v) {
        $(v).insertAfter(old_start);
      });
    });

    //**Pjax End**
    $(document).on('pjax:end', '#js-pageContent', function() {
      // Closes global search and nav menus in mobile
      globalSearchForm.pjax_end();

      // if we've gotten to a page without search context, clear the query manager
      if(!$('#js-facet').length && !$('#js-objectViewport').length) {
        qm.clear({silent: true});
      }

      //Create/destroy components based on which selectors are available in the DOM,
      //which components exist already, and which selectors are no longer in the DOM
      setupComponents(globalSearchForm, qm);
      globalSearchForm.popstate = null;
    });

    //**Loading notifications**
    /* globals NProgress: false */
    $(document).on('pjax:send', function() {
      NProgress.start();
    });

    $(document).on('pjax:complete', function() {
      NProgress.done();
    });

    $(document).on('pjax:popstate', function(e) {
      globalSearchForm.popstate = e.direction;
    });
  }
});


var on_ready_pjax_end_handler = function() {
  // send google analytics on pjax pages 
  /* globals ga: false */
  /* jshint latedef: false */
  if (typeof ga !== 'undefined') {
    var inst_ga_code = $('[data-ga-code]').data('ga-code');
    var dim1 = $('[data-ga-dim1]').data('ga-dim1');
    var dim2 = $('[data-ga-dim2]').data('ga-dim2');
    var dim3 = Modernizr.sessionstorage.toString();
    var dim4 = $('[data-ga-dim4]').data('ga-dim4');

    ga('set', 'location', window.location.href);
    if (dim1) { ga('set', 'dimension1', dim1); }
    if (dim2) { ga('set', 'dimension2', dim2); }
    if (dim3) { ga('set', 'dimension3', dim3); }
    if (dim4) { ga('set', 'dimension4', dim4); }
    ga('send', 'pageview');
    if (inst_ga_code) {
      var inst_tracker_name = inst_ga_code.replace(/-/g,'x');
      ga('create', inst_ga_code, 'auto', {'name': inst_tracker_name});
      ga(inst_tracker_name + '.set', 'anonymizeIp', true);
      ga(inst_tracker_name + '.set', 'location', window.location.href);
      if (dim1) { ga(inst_tracker_name + '.set', 'dimension1', dim1); }
      if (dim2) { ga(inst_tracker_name + '.set', 'dimension2', dim2); }
      ga( inst_tracker_name + '.send', 'pageview');
    }
  }

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
};
$(document).on('pjax:end', on_ready_pjax_end_handler)

//************************************

// No support for background-blend-mode
if(!('backgroundBlendMode' in document.body.style)) {
  var html = document.getElementsByTagName('html')[0];
  html.className = html.className + ' no-background-blend-mode';
}
