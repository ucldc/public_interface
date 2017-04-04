/*global Backbone */
/*exported CarouselView */

'use strict';

var CarouselView = Backbone.View.extend({
  el: $('#js-pageContent'),
  carouselRows: 16,
  carouselConfig: {
    infinite: true,
    speed: 300,
    variableWidth: true,
    lazyLoad: 'ondemand'
  },

  events: {
    'click #js-linkBack'             : 'goToSearchResults',
    'beforeChange .carousel'         : 'loadSlides',
    'click .js-item-link'            : 'goToItemPage',
    'click .js-rc-page'              : 'paginateRelatedCollections',
    'click .js-relatedCollection'    : 'goToCollectionPage'
  },

  goToSearchResults: function(e) {
    // Middle click, cmd click, and ctrl click should open links in a new tab as normal.
    if ( e.which > 1 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey ) { return; }

    // Unset carousel specific information
    this.model.unsetCarouselInfo();

    e.preventDefault();
    $.pjax({
      url: $(e.currentTarget).children('a').attr('href').split('?')[0],
      container: '#js-pageContent',
      data: this.model.toJSON(),
      traditional: true
    });
  },

  loadSlides: function(e, slick, currentSlide, nextSlide) {
    var numFound = $('#js-carousel').data('numfound');
    var numLoaded = $('.carousel').slick('getSlick').slideCount;
    var slidesToScroll = slick.options.slidesToScroll;
    var data_params;

    //PREVIOUS BUTTON PRESSED
    if (
      (currentSlide > nextSlide && (nextSlide !== 0 || currentSlide === slidesToScroll)) || 
      (currentSlide === 0 && nextSlide > slick.slideCount - slidesToScroll && nextSlide < slick.slideCount)) {
      if (numLoaded < numFound && $('[data-item_number=0]').length === 0) {
        if (parseInt(this.carouselStart) - parseInt(this.carouselRows) > 0) {
          this.carouselStart = parseInt(this.carouselStart) - parseInt(this.carouselRows);
          data_params = this.toJSON();
        } else {
          data_params = this.toJSON();
          data_params.rows = this.carouselStart;
          this.carouselStart = data_params.start = 0;
        }
        delete data_params.itemNumber;

        $.ajax({data: data_params, traditional: true, url: '/carousel/', success: function(data) {
            $('.carousel').slick('slickAdd', data, true);
        }});
      }
    }
    //NEXT BUTTON PRESSED
    else {
      if (numLoaded < numFound && $('[data-item_number=' + String(numFound-1) + ']').length === 0) {
        this.carouselEnd = parseInt(this.carouselEnd) + parseInt(this.carouselRows);
        data_params = this.toJSON();
        data_params.start = this.carouselEnd;
        delete data_params.itemNumber;

        $.ajax({data: data_params, traditional: true, url: '/carousel/', success: function(data) {
            $('.carousel').slick('slickAdd', data);
        }});
      }
    }
  },
  goToItemPage: function(e) {
    // Middle click, cmd click, and ctrl click should open
    // links in a new tab as normal.
    if ( e.which > 1 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey ) { return; }

    if ($(e.currentTarget).data('item_number') !== undefined) {
      this.model.set({
        itemNumber: $(e.currentTarget).data('item_number'),
        itemId: $(e.currentTarget).data('item_id')
      }, {silent: true});

      // add implicit context for campus, institution, and collection pages
      if($('#js-institution').length > 0) {
        if($('#js-institution').data('campus')) {
          this.model.set({campus_slug: $('#js-institution').data('campus')}, {silent: true});
        } else {
          this.model.set({repository_data: $('#js-institution').data('institution')}, {silent: true});
        }
      } else if ($('#js-collection').length > 0) {
        this.model.set({collection_data: $('#js-collection').data('collection')}, {silent: true});
      }

      e.preventDefault();
      $.pjax({
        url: $(e.currentTarget).attr('href'),
        container: '#js-itemContainer'
      });
    }
  },
  paginateRelatedCollections: function(e) {
    var data_params = this.model.toJSON();
    delete data_params.itemId;
    delete data_params.itemNumber;
    delete data_params.referral;
    delete data_params.referralName;
    if (e !== undefined) {
      data_params.rc_page = $(e.currentTarget).data('rc_page');
    } else {
      data_params.rc_page = 0;
    }
    //TODO: function(data, status, jqXHR)
    $.ajax({data: data_params, traditional: true, url: '/relatedCollections/', success: function(data) {
        $('#js-relatedCollections').html(data);
      }
    });
  },

  goToCollectionPage: function() {
    this.model.clear({silent: true});
  },

  toJSON: function() {
    var context = this.model.toJSON();
    context.start = this.carouselStart;
    context.rows = this.carouselRows;
    return context;
  },

  changeWidth: function() {
    var visibleCarouselWidth = $('#js-carousel .slick-list').prop('offsetWidth');
    var currentSlide = $('.js-carousel_item[data-slick-index=' + $('.carousel').slick('slickCurrentSlide') + ']');
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

    $('.carousel').slick('slickSetOption', 'slidesToShow', numPartialThumbs, false);
    $('.carousel').slick('slickSetOption', 'slidesToScroll', numFullThumbs, true);
  },

  initCarousel: function() {
    if (this.model.get('itemNumber') !== undefined) {
      this.carouselStart = this.carouselEnd = this.model.get('itemNumber');
    }

    var data_params = this.toJSON();
    delete data_params.itemNumber;
    data_params.init = true;

    //TODO: function(data, status, jqXHR)
    $.ajax({
      url: '/carousel/',
      data: data_params,
      traditional: true,
      success: (function(that) {
        return function(data) {
          $('#js-carouselContainer').html(data);
          $('.carousel').show();
          $('.carousel').slick(that.carouselConfig);
          that.changeWidth();
        };
      }(this))
    });
  },

  initialize: function() {
    this.model.set({itemId: $('#js-itemContainer').data('itemid')}, {silent: true});
    this.initCarousel();
    this.paginateRelatedCollections();
  },

  destroy: function() {
    this.undelegateEvents();
  }
});
