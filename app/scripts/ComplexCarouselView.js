/*global Backbone, imagesLoaded */
/*exported ComplexCarouselView */

'use strict';

// component created if selector in DOM, selector is in the following templates (2017-04-04)
// selector: .carousel-complex
// templates: complex-object.html

var ComplexCarouselView = Backbone.View.extend({
  el: $('#js-pageContent'),
  carouselConfig: {
    infinite: false,
    speed: 300,
    variableWidth: true,
    slidesToShow: 8,
    slidesToScroll: 8,
    lazyLoad: 'ondemand'
  },

  events: {
    'click .js-set-link'        : 'getSet',
    'click .js-component-link'  : 'getComponent',
    'afterChange .carousel-complex__item-container': 'afterChange'
  },
  // events: {'click .js-set-link': 'getSet'}
  getSet: function(e) {
    // Middle click, cmd click, and ctrl click should open
    // links in a new tab as normal.
    if ( e.which > 1 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey ) { return; }

    e.preventDefault();
    $.pjax({
      type: 'GET',
      url: $(e.currentTarget).attr('href'),
      container: '#js-itemContainer',
      traditional: true,
      scrollTo: 440
    });
  },
  // events: {'click .js-component-link': 'getComponent'}
  getComponent: function(e) {
    // Middle click, cmd click, and ctrl click should open
    // links in a new tab as normal.
    if ( e.which > 1 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey ) { return; }

    var data_params = {order: $(e.currentTarget).data('item_id')};

    e.preventDefault();
    $.pjax({
      type: 'GET',
      url: $(e.currentTarget).attr('href').split('?')[0],
      container: '#js-itemContainer',
      data: data_params,
      traditional: true,
      scrollTo: 440
    });
  },
  // events: {'afterChange .carousel-complex__item-container': 'afterChange'}
  afterChange: function(e, slick) {
    this.changeWidth(e, slick);
    this.checkEdges(e, slick);
  },

  checkEdges: function(e, slick) {
    if (slick === undefined) {
      slick = $('.carousel-complex__item-container').slick('getSlick');
    }

    if (slick.slickCurrentSlide() !== 0 && slick.slickCurrentSlide() < slick.getOption('slidesToScroll')) {
      slick.setOption('slidesToScroll', slick.slickCurrentSlide(), true);
    }

    //There seems to be some sort of off-by-one issue with slidesToScroll
    if (slick.slickCurrentSlide() + slick.getOption('slidesToScroll') + 1 === slick.slideCount) {
      slick.setOption('slidesToShow', 1, false);
      slick.setOption('slidesToScroll', 1, true);
    }
  },

  changeWidth: function(e, slick) {
    if (slick === undefined) {
      slick = $('.carousel-complex__item-container').slick('getSlick');
    }

    var visibleCarouselWidth = $('.carousel-complex__item-container .slick-list').prop('offsetWidth');
    var currentSlide = $('.carousel-complex__item-container [data-slick-index=' + slick.slickCurrentSlide() + ']');
    var displayedCarouselPx = currentSlide.outerWidth() + parseInt(currentSlide.css('margin-right'));
    var numPartialThumbs = 1, numFullThumbs = 0;

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

  initCarousel: function() {
    $('.carousel-complex').show();
    $('.carousel-complex__item-container').slick(this.carouselConfig);
    if ($('.carousel-complex__item--selected').length > 0) {
      $('.carousel-complex__item-container').slick('slickGoTo', $('.carousel-complex__item--selected').data('slick-index'));
    }
  },

  pjax_end: function(that) {
    return function() {
      if ($('.carousel-complex').is(':hidden')) {
        that.initialize();
      }
    };
  },

  initialize: function() {
    this.initCarousel();
    imagesLoaded('.carousel-complex__item-container img', (function(that) {
      return function() {
        that.changeWidth();
      };
    }(this)));

    $(document).on('pjax:end', '#js-pageContent', this.pjax_end(this));
  },

  destroy: function() {
    $(document).off('pjax:end', '#js-pageContent', this.pjax_end(this));
    this.undelegateEvents();
  }
});
