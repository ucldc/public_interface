/*global Backbone */
/*exported ItemView */

'use strict';

// Component created if **#js-carouselContainer** in DOM
// templates that include `#js-carouselContainer`: `itemView.html`

var ItemView = Backbone.View.extend({
  el: $('#js-pageContent'),
  // Carousel Configuration options we'll use later
  carouselRows: 16,
  carouselConfig: {
    infinite: true,
    speed: 300,
    variableWidth: true,
    lazyLoad: 'ondemand'
  },

  // User Event Handlers
  //----------------------
  // These are event handlers for user interaction with the carousel,
  // surrounding links, and the related collections

  events: {
    'click #js-linkBack'             : 'goToSearchResults',
    'beforeChange .carousel'         : 'loadSlides',
    'click .js-item-link'            : 'goToItemPage',
    'click .js-rc-page'              : 'paginateRelatedCollections',
    'click .js-relatedCollection'    : 'clearQuery',
    'click .js-disqus'               : 'initDisqus'
  },

  // `click` triggered on `#js-linkBack`
  // This is the 'return to search results', 'return to <Collection>', or
  // 'return to <Institution>' link that appears above the carousel on the right
  goToSearchResults: function(e) {
    // Middle click, cmd click, and ctrl click should open links in a new tab as normal.
    if ( e.which > 1 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey ) { return; }

    // Unset carousel/item specific information
    this.model.unsetItemInfo();

    e.preventDefault();
    $.pjax({
      url: $(e.currentTarget).children('a').attr('href').split('?')[0],
      container: '#js-pageContent',
      data: this.model.toJSON(),
      traditional: true
    });
  },

  // `beforeChange` triggered on `.carousel`
  // lazy-loading slides on pagination of the carousel
  loadSlides: function(e, slick, currentSlide, nextSlide) {
    var numFound = $('#js-carousel').data('numfound');
    var numLoaded = $('.carousel').slick('getSlick').slideCount;
    var slidesToScroll = slick.options.slidesToScroll;
    var data_params;

    //PREVIOUS BUTTON PRESSED
    //retrieve previous slides in search results
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
    //retrieve next slides in search results
    else {
      if (numLoaded < numFound && $('[data-item_number=' + String(numFound-1) + ']').length === 0) {
        this.carouselEnd = parseInt(this.carouselEnd||0) + parseInt(this.carouselRows||0);
        data_params = this.toJSON();
        data_params.start = this.carouselEnd;
        delete data_params.itemNumber;

        $.ajax({data: data_params, traditional: true, url: '/carousel/', success: function(data) {
            $('.carousel').slick('slickAdd', data);
        }});
      }
    }
  },

  // `click` triggered on `.js-item-link`
  // when the user clicks an item in the carousel, navigate to that item
  // and update the query manager
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

  // `click` triggered on `.js-rc-page`
  paginateRelatedCollections: function(e) {
    var data_params = this.model.toJSON();
    // don't need carousel specific item data for the related collections
    delete data_params.itemId;
    delete data_params.itemNumber;
    delete data_params.referral;
    delete data_params.referralName;
    if (e !== undefined) {
      data_params.rc_page = $(e.currentTarget).data('rc_page');
    } else {
      data_params.rc_page = 0;
    }
    // regular ajax request - we don't need pushState on the url here
    $.ajax({data: data_params, traditional: true, url: '/relatedCollections/', success: function(data) {
        $('#js-relatedCollections').html(data);
      }
    });
  },

  // `click` triggered on `.js-relatedCollection`
  clearQuery: function() {
    this.model.clear({silent: true});
  },

  // HELPER METHODS
  // --------------------

  // method adds `start` and `rows` to pjax and ajax queries.
  // this is specific to which item is selected in the carousel.
  toJSON: function() {
    var context = this.model.toJSON();
    context.start = this.carouselStart || 0;
    context.rows = this.carouselRows;
    return context;
  },

  // When the width changes, we have to change the carousel's slidesToShow
  // and slidesToScroll options (can't scroll by 8 in mobile mode)
  changeWidth: function() {
    var visibleCarouselWidth = $('#js-carousel .slick-list').prop('offsetWidth');
    var currentSlide = $('.js-carousel_item[data-slick-index=' + $('.carousel').slick('slickCurrentSlide') + ']');
    var displayedCarouselPx = currentSlide.outerWidth() + parseInt(currentSlide.css('margin-right'));
    var numPartialThumbs = 1, numFullThumbs = 0;

    // count full thumbnails visible, and partial thumbnails visible
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

  // get the first set of slides for the carousel
  initCarousel: function() {
    if (this.model.get('itemNumber') !== undefined) {
      this.carouselStart = this.carouselEnd = this.model.get('itemNumber');
    }

    var data_params = this.toJSON();
    delete data_params.itemNumber;
    data_params.init = true;

    // simple AJAX call to get the first set of carousel items
    // success callback puts the data into the carousel div,
    // initiates slick, and calls changeWidth to set slidesToScroll
    // and slidesToShow options based on current window width
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

  // add the media element player if necessary
  initMediaPlayer: function() {
    if($('#obj__mejs').length) {
      if (this.mediaplayer) {
        if (!this.mediaplayer.paused) {
          this.mediaplayer.pause();
        }
        this.mediaplayer.remove();
        delete this.mediaplayer;
      }

      $('.media-player').mediaelementplayer({
        stretching: 'responsive',
        success: (function(that) {
          return function(mediaElement, originalNode, instance) {
            that.mediaplayer = instance;
          };
        }(this))
      });
    }
  },

  initDisqus: function() {
    $('#disqus_thread').empty();
    $('#disqus_thread').addClass('comment');
    var disqus_shortname = $('#disqus_loader').data('disqus');
    $.ajaxSetup({cache:true});
    $.getScript('http://' + disqus_shortname + '.disqus.com/embed.js');
    $.ajaxSetup({cache:false});
    $('#disqus_loader').hide();
  },

  // PJAX EVENT HANDLERS
  // ---------------------

  // called on `pjax:beforeSend`
  // Navigating between item pages is one of the rare cases where instead of
  // replacing the contents of  #js-pageContent with the results of a pjax call,
  // we replace the contents of #js-itemContainer. When a user clicks from an
  // item page to another item page, this event handler appends a special header
  // to tell the server to use a different template
  // (`/calisphere/templates/calisphere/pjaxTemplates/pjax-item.html`)
  // for the response
  pjax_beforeSend: function(e, xhr) {
    xhr.setRequestHeader('X-From-Item-Page', 'true');
  },

  // called on `pjax:end`
  pjax_end: function(that) {
    return function() {
      // reset the query manager's item-specific info to the previous item.
      if (that.popstate === 'back' || that.popstate === 'forward') {
        var queryObj;
        if ($('#js-carouselForm').length) {
          queryObj = that.model.getItemInfoFromDOM();
          that.model.set(queryObj, {silet: true});
        }

        if ($('#disqus_thread').html().length > 0) {
          that.initDisqus();
        }
        that.popstate = null;
      }

      // when navigating between items, the carousel is *not* a part of the #js-itemContainer
      // document fragment returned, so here we manually change which item in the carousel
      // gets the 'selected' CSS treatment
      var lastItem = $('.carousel__item--selected');
      if (lastItem.children('a').data('item_id') !== that.model.get('itemId')) {
        lastItem.find('.carousel__image--selected').toggleClass('carousel__image');
        lastItem.find('.carousel__image--selected').toggleClass('carousel__image--selected');
        lastItem.toggleClass('carousel__item');
        lastItem.toggleClass('carousel__item--selected');

        var linkItem = $('.js-item-link[data-item_id="' + that.model.get('itemId') + '"]');
        linkItem.find('.carousel__image').toggleClass('carousel__image--selected');
        linkItem.find('.carousel__image').toggleClass('carousel__image');
        linkItem.parent().toggleClass('carousel__item--selected');
        linkItem.parent().toggleClass('carousel__item');
      }

      that.initMediaPlayer();
    };
  },

  pjax_popstate: function(that) {
    return function(e) {
      that.popstate = e.direction;
    };
  },

  // called via `setupComponents()` on document.ready() and pjax:end
  initialize: function() {
    // gets the query from the DOM, if present
    if ($('#js-carouselForm').length) {
      var queryObj = this.model.getQueryFromDOM('js-carouselForm');
      queryObj = $.extend(queryObj, this.model.getItemInfoFromDOM());
      this.model.set(queryObj, {silent: true});
    } else {
      this.model.set({itemId: $('#js-itemContainer').data('itemid')}, {silent: true});
    }
    // initializes the carousel and the related collections
    this.initCarousel();
    this.paginateRelatedCollections();
    this.initMediaPlayer();

    // bind pjax handlers to `this`
    // we need to save the bound handler to `this.bound_pjax_end` so we can later
    // remove these handlers by name in `destroy`
    this.bound_pjax_end = this.pjax_end(this);
    this.bound_pjax_popstate = this.pjax_popstate(this);
    $(document).on('pjax:beforeSend', '#js-itemContainer', this.pjax_beforeSend);
    $(document).on('pjax:end', '#js-itemContainer', this.bound_pjax_end);
    $(document).on('pjax:popstate', '#js-pageContent', this.bound_pjax_popstate);
  },

  destroy: function() {
    // remove pjax event handlers
    $(document).off('pjax:beforeSend', '#js-itemContainer', this.pjax_beforeSend);
    $(document).off('pjax:end', '#js-itemContainer', this.bound_pjax_end);
    $(document).off('pjax:popstate', '#js-pageContent', this.bound_pjax_popstate);

    // undelegate all user event handlers specified in `this.events`
    this.undelegateEvents();

    // remove item-specific information from the query manager
    this.model.unsetItemInfo();
  }
});
