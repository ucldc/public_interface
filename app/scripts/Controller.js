/*global ContactOwnerFormView, OpenSeadragon, tileSources, ExhibitPageView, FacetFormView, ItemView, ComplexCarouselView */
/*exported setupComponents */

'use strict';

// Component Controller
// ---------------------

// `setupComponents()` acts as a controller to create/destroy JS components 
// based on which selectors are available/no longer available in the DOM.
// `setupComponents()` is called on `$(document).ready()` and also on `pjax:end`.
// https://github.com/defunkt/jquery-pjax#events

var setupComponents = function(globalSearchForm, qm) {
  // **CALISPHERE COMPONENTS**

  // Calisphere components are subclasses of Backbone.js `Backbone.View` and 
  // are attached to the `globalSearchForm` namespace, an instance of the
  // `GlobalSearchForm` component. Their model (where applicable) is `qm`, an
  // instance of the `QueryManager`.

  // Calisphere components all have constructors (called using the new 
  // keyword here) as well as a `destroy` function. Additionally, each has 
  // pjax event handlers (bound in that component's initializer, and unbound 
  // in `destroy`), as well as various user-action handlers - click, submit, etc. 

  if ($('#js-facet').length) {
    globalSearchForm.facetForm = globalSearchForm.facetForm || new FacetFormView({model: qm, popstate: globalSearchForm.popstate});
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

  // **VENDOR INITIALIZATION**
  
  // These JS components are classes imported from external libraries and 
  // don't need their own Calisphere-specific componentry beyond the options
  // available in their initialization. 
  
  // **OpenSeadragon Viewer for hosted image content**
  if($('#obj__osd').length) {
    // Unlike some other components, the viewer leaves behind some cruft, 
    // so we cannot just reuse the same viewer for different images.
    // Instead we have to destroy the previous viewer (if one exists), 
    // and create a new one
    if(globalSearchForm.viewer) {
      globalSearchForm.viewer.destroy();
      delete globalSearchForm.viewer;
      $('#obj__osd').empty();
    }
    if ($('.openseadragon-container').length) { $('.openseadragon-container').remove(); }
    globalSearchForm.viewer = new OpenSeadragon({
      id: 'obj__osd',
      toolbar: 'obj__osd-toolbar',
      tileSources: [tileSources],
      zoomInButton: 'obj__osd-button-zoom-in',
      zoomOutButton: 'obj__osd-button-zoom-out',
      homeButton: 'obj__osd-button-home',
      fullPageButton: 'obj__osd-button-fullscreen',
      rotateLeftButton: 'obj__osd-button-rotate-left',
      rotateRightButton: 'obj__osd-button-rotate-right',
      showRotationControl: true
    });

    globalSearchForm.viewer.addHandler('home', function (data) {
        data.eventSource.viewport.setRotation(0);
    });

  } 
  // if the viewer exists, but the hosted image content 
  // selector `#obj__osd` does not, then just destroy the viewer
  else if (globalSearchForm.viewer) {
    globalSearchForm.viewer.destroy();
    delete globalSearchForm.viewer;
  }

  // **Isotope Masonry grid for Exhibitions random explore page**
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

  // **Text Truncation**

  //Item page, item title
  $('.obj__heading').dotdotdot({
    ellipsis: '…',
    watch: 'window',
    height: 50,
    lastCharacter: { // remove these characters from the end of the truncated text:
      remove: [ ' ', ',', ';', '.', '!', '?', '[', ']' ]
    }
  });
  //Search results page, item title
  $('.thumbnail__caption').dotdotdot({
    ellipsis: '…',
    watch: 'window',
    height: 30,
    lastCharacter: {
      remove: [ ' ', ',', ';', '.', '!', '?', '[', ']' ]
    }
  });
  //Item page, carousel, item title
  $('.carousel__thumbnail-caption').dotdotdot({
    ellipsis: '…',
    watch: 'window',
    height: 30,
    lastCharacter: {
      remove: [ ' ', ',', ';', '.', '!', '?', '[', ']' ]
    }
  });

  // **Infinite Scroll on Collection Browse pages**
  
  // Collections A-Z, Collections Random Explore, 
  // and Collections at <institution> Pages
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
