/*global Backbone, imagesLoaded */
/*exported ComplexCarouselView */

'use strict';

// Component created if **.carousel-complex** in DOM    
// templates that include `.carousel-complex`: `complex-object.html`

var ComplexCarouselView = Backbone.View.extend({
  el: $('#js-pageContent'),
  carouselConfig: {
    infinite: false,
    speed: 300,
    variableWidth: true,
    slidesToShow: 15,
    slidesToScroll: 15,
    lazyLoad: 'ondemand'
  },

  // User Event Handlers
  // ---------------------
  
  events: {
    'click .js-set-link'        : 'getSet',
    'click .js-component-link'  : 'getComponent',
    'afterChange .carousel-complex__item-container': 'afterChange'
  },
  // `click` triggered on `.js-set-link`    
  // this is the link fixed at the start of the complex object
  // carousel which gets metadata information for the full 
  // complex object
  getSet: function(e) {
    // Middle click, cmd click, and ctrl click should open
    // links in a new tab as normal.
    if ( e.which > 1 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey ) { return; }

    e.preventDefault();
    // pjax replacement - previously did a scrollTo 440px after this
    document.location = $(e.currentTarget).attr('href')
  },
  
  // `click` triggered on `.js-component-link`    
  // retrieve a particular component by adding order parameter
  getComponent: function(e) {
    // Middle click, cmd click, and ctrl click should open
    // links in a new tab as normal.
    if ( e.which > 1 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey ) { return; }

    var data_params = {order: $(e.currentTarget).data('item_id')};

    e.preventDefault();
    // pjax replacement - previously did a scrollTo 440px after this
    document.location = $(e.currentTarget).attr('href').split('?')[0] + 
      '?' + $.param(data_params, true);
  },
  
  // `afterChange` triggered on `.carousel-complex__item-container`
  // slick event called after slides scroll
  afterChange: function(e, slick) {
    this.changeWidth(e, slick);
    this.checkEdges(e, slick);
  },

  // HELPER FUNCTIONS
  // ------------------
  
  checkEdges: function(e, slick) {
    // retrieve slick carousel
    if (slick === undefined) {
      slick = $('.carousel-complex__item-container').slick('getSlick');
    }
    
    // not sure what this does
    if (slick.slickCurrentSlide() !== 0 && slick.slickCurrentSlide() < slick.getOption('slidesToScroll')) {
      slick.setOption('slidesToScroll', slick.slickCurrentSlide(), true);
    }

    // There seems to be some sort of off-by-one issue with slidesToScroll
    // this seems to ensure you can get *all the way* to the end of a set of component objects
    if (slick.slickCurrentSlide() + slick.getOption('slidesToScroll') + 1 === slick.slideCount) {
      slick.setOption('slidesToShow', 1, false);
      slick.setOption('slidesToScroll', 1, true);
    }
  },

  // As slides load, change the slidesToShow and slidesToScroll options
  // dynamically. Each slide is a variable width, only constrained by height
  // so this changes every time. 
  changeWidth: function(e, slick) {
    if (slick === undefined) {
      slick = $('.carousel-complex__item-container').slick('getSlick');
    }

    var visibleCarouselWidth = $('.carousel-complex__item-container .slick-list').prop('offsetWidth');
    var currentSlide = $('.carousel-complex__item-container [data-slick-index=' + slick.slickCurrentSlide() + ']');
    var displayedCarouselPx = currentSlide.outerWidth() + parseInt(currentSlide.css('margin-right'));
    var numPartialThumbs = 1, numFullThumbs = 0;

    // count number of thumbnails and partial thumbnails visible in carousel
    while (displayedCarouselPx < visibleCarouselWidth && currentSlide.length > 0) {
      numFullThumbs++;
      currentSlide = currentSlide.next();
      //if more than just the next slide's left margin is displayed, then numPartialThumbs++
      if (visibleCarouselWidth - displayedCarouselPx > parseInt(currentSlide.css('margin-left'))) {
        numPartialThumbs++;
      }
      displayedCarouselPx = displayedCarouselPx + currentSlide.outerWidth(true);
    }

    //if everything but the last slide's right margin is displayed, then numFullThumbs++
    if (displayedCarouselPx - visibleCarouselWidth < parseInt(currentSlide.css('margin-right'))) {
      numFullThumbs++;
    }

    slick.slickSetOption('slidesToShow', numPartialThumbs, false);
    slick.slickSetOption('slidesToScroll', numFullThumbs, true);
  },

  // initialize the carousel
  initCarousel: function() {
    $('.carousel-complex').show();
    $('.carousel-complex__item-container').slick(this.carouselConfig);
    if ($('.carousel-complex__item--selected').length > 0) {
      $('.carousel-complex__item-container').slick('slickGoTo', $('.carousel-complex__item--selected .carousel-complex__link').data('item_id'));
    } else if ($('.carousel-complex__tile--selected').length > 0) {
      $('.carousel-complex__item-container').slick('slickGoTo', $('.carousel-complex__tile--selected .carousel-complex__link').data('item_id'));
    }
  },

  // called by `setupComponents()` on `$(document).ready()`
  initialize: function() {
    this.initCarousel();
    // once the images have loaded, change slidesToShow and slidesToScroll to 
    // reflect the actual number of slides visible in the carousel
    imagesLoaded('.carousel-complex__item-container img', (function(that) {
      return function() {
        that.changeWidth();
      };
    }(this)));
  },

  destroy: function() {
    this.undelegateEvents();
  }
});
