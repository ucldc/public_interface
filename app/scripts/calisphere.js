/*global QueryManager, GlobalSearchFormView, ContactOwnerFormView, OpenSeadragon, tileSources, ExhibitPageView, FacetFormView, ItemView, ComplexCarouselView */

/* globals Modernizr: false */
'use strict';

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

if(typeof console === 'undefined') {
  console = { log: function() { } };
}

$(document).on('pjax:timeout', function() { return false; });

var qm, globalSearchForm;

var setupComponents = function() {
  /*********** CALISPHERE COMPONENTS *****************/
  if ($('#js-facet').length) {
    globalSearchForm.facetForm = globalSearchForm.facetForm || new FacetFormView({model: qm});
  } else if (globalSearchForm.facetForm) {
    globalSearchForm.facetForm.destroy();
    delete globalSearchForm.facetForm;
  }

  if ($('#js-carouselContainer').length) {
    globalSearchForm.carousel = globalSearchForm.carousel || new ItemView({model: qm});
  } else if (globalSearchForm.carousel) {
    globalSearchForm.carousel.destroy();
    delete globalSearchForm.carousel;
  }

  if($('#js-contactOwner').length) {
    globalSearchForm.contactOwnerForm = globalSearchForm.contactOwnerForm || new ContactOwnerFormView();
  } else if (globalSearchForm.contactOwnerForm) {
    delete globalSearchForm.contactOwnerForm;
  }

  if($('.carousel-complex').length) {
    globalSearchForm.complexCarousel = globalSearchForm.complexCarousel || new ComplexCarouselView({model: qm});
  } else if (globalSearchForm.complexCarousel) {
    globalSearchForm.complexCarousel.destroy();
    delete globalSearchForm.complexCarousel;
  }

  if($('#js-exhibit-title').length) {
    globalSearchForm.exhibitPage = globalSearchForm.exhibitPage || new ExhibitPageView();
  } else if (globalSearchForm.exhibitPage) {
    globalSearchForm.exhibitPage.destroy();
    delete globalSearchForm.exhibitPage;
  }

  /************ VENDOR INITIALIZATION ****************/
  if($('#obj__osd').length) {
    if(globalSearchForm.viewer) {
      globalSearchForm.viewer.destroy();
      delete globalSearchForm.viewer;
      $('#obj__osd').empty();
    }
    if ($('.openseadragon-container').length) { $('.openseadragon-container').remove(); }
    globalSearchForm.viewer = new OpenSeadragon({
      id: 'obj__osd',
      tileSources: [tileSources],
      zoomInButton: 'obj__osd-button-zoom-in',
      zoomOutButton: 'obj__osd-button-zoom-out',
      homeButton: 'obj__osd-button-home',
      fullPageButton: 'obj__osd-button-fullscreen'
    });
  } else if (globalSearchForm.viewer) {
    globalSearchForm.viewer.destroy();
    delete globalSearchForm.viewer;
  }

  if($('#js-exhibit-wrapper').length) {
    globalSearchForm.grid = $('#js-exhibit-wrapper').isotope({
      layoutMode: 'masonry',
      itemSelector: '.js-grid-item',
      percentPosition: true,
      masonry: {
        columnWidth: '.js-grid-sizer'
      }
    });
  }

  $('.obj__heading').dotdotdot({
    ellipsis: '…',
    watch: 'window',
    height: 50,
    lastCharacter: { // remove these characters from the end of the truncated text:
      remove: [ ' ', ',', ';', '.', '!', '?', '[', ']' ]
    }
  });
  $('.thumbnail__caption').dotdotdot({
    ellipsis: '…',
    watch: 'window',
    height: 30,
    lastCharacter: {
      remove: [ ' ', ',', ';', '.', '!', '?', '[', ']' ]
    }
  });
  $('.carousel__thumbnail-caption').dotdotdot({
    ellipsis: '…',
    watch: 'window',
    height: 30,
    lastCharacter: {
      remove: [ ' ', ',', ';', '.', '!', '?', '[', ']' ]
    }
  });

  //if we've gotten to a page with a list of collection mosaics, init infinite scroll
  if($('#js-mosaicContainer').length) {
    $('#js-mosaicContainer').infinitescroll({
      navSelector: '#js-collectionPagination',
      nextSelector: '#js-collectionPagination a.js-next',
      itemSelector: '#js-mosaicContainer div.js-collectionMosaic',
      debug: false,
      loading: {
        finishedMsg: 'All collections showing.',
        img: '//calisphere.org/static_root/images/orange-spinner.gif',
        msgText: '',
        selector: '#js-loading'
      }
    });
  }
};

$(document).ready(function() {
  if (typeof ga !== 'undefined') {
    // google event tracking track outbound links
    // based on https://support.google.com/analytics/answer/1136920?hl=en
    // capture the click handler on outbound links
    $('body').on('click', 'a[href^="http://"], a[href^="https://"]', function() {
      var url = $(this).attr('href');
      ga('send', 'event', 'outbound', 'click', url, {
        'transport': 'beacon',  // use navigator.sendBeacon
        // click captured and tracked, send the user along
        'hitCallback': function () {
          document.location = url;
        }
      });
      return false;
    });

    $('.button__contact-owner').on('click', function() {
      ga('send', 'event', 'buttons', 'contact', event.target.href, {
        'transport': 'beacon',  // use navigator.sendBeacon
        // click captured and tracked, send the user along
        'hitCallback': function () {
          document.location = event.target.href;
        }
      });
      return false;
    });
  }
  sessionStorageWarning();

  // http://stackoverflow.com/questions/5489946/jquery-how-to-wait-for-the-end-of-resize-event-and-only-then-perform-an-ac
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

  if (!$('.home').length) {
    $.pjax.defaults.timeout = 5000;
    $(document).pjax('a[data-pjax=js-pageContent]', '#js-pageContent');

    //on page load, create a query manager and global search form
    qm = new QueryManager();
    globalSearchForm = new GlobalSearchFormView({model: qm});
    setupComponents();

    $(document).on('pjax:success', function(e, data, x, xhr, z) {
      var start_marker = z.context.find('meta[property=og\\:type]');
      var variable_markup = start_marker.nextUntil($('meta[name=twitter\\:creator]'));
      var old_start = $('head').find('meta[property=og\\:type]');
      old_start.nextUntil($('meta[name=twitter\\:creator]')).remove();
      $.each($(variable_markup).get().reverse(), function(i, v) {
        $(v).insertAfter(old_start);
      });
    });

    $(document).on('pjax:end', '#js-pageContent', function() {
      globalSearchForm.pjax_end();

      // if we've gotten to a page without search context, clear the query manager
      if(!$('#js-facet').length && !$('#js-objectViewport').length) {
        qm.clear({silent: true});
      }

      setupComponents();
    });

    /* globals NProgress: false */
    $(document).on('pjax:send', function() {
      NProgress.start();
    });

    $(document).on('pjax:complete', function() {
      NProgress.done();
    });
  }


});


$(document).on('ready pjax:end', function() {
  // send google analytics on pjax pages
  /* globals ga: false */
  /* jshint latedef: false */
  if (typeof ga !== 'undefined') {
    var inst_ga_code = $('[data-ga-code]').data('ga-code');
    var dim1 = $('[data-ga-dim1]').data('ga-dim1');
    var dim2 = $('[data-ga-dim2]').data('ga-dim2');
    var dim3 = Modernizr.sessionstorage.toString();

    ga('set', 'location', window.location.href);
    if (dim1) { ga('set', 'dimension1', dim1); }
    if (dim2) { ga('set', 'dimension2', dim2); }
    if (dim3) { ga('set', 'dimension3', dim3); }
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

  // collection title search

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
});

if(!('backgroundBlendMode' in document.body.style)) {
    // No support for background-blend-mode
  var html = document.getElementsByTagName('html')[0];
  html.className = html.className + ' no-background-blend-mode';
}
