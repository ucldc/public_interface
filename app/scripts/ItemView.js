/*global Backbone, DISQUS, ga */
/*exported ItemView */

'use strict';

// Component created if **#js-carouselContainer** in DOM
// templates that include `#js-carouselContainer`: `itemView.html`

var ItemView = Backbone.View.extend({
  el: $('#js-pageContent'),
  // Carousel Configuration options we'll use later
  // update to 1.8.1 added nested divs. Added rows: 0 per 
  // https://github.com/kenwheeler/slick/issues/3110
  carouselRows: 8,
  carouselConfig: {
    infinite: false,
    speed: 300,
    variableWidth: true,
    lazyLoad: 'ondemand', 
    rows: 0
  },

  // User Event Handlers
  //----------------------
  // These are event handlers for user interaction with the carousel,
  // surrounding links, and the related collections

  events: {
    'click #js-linkBack'                : 'goToSearchResults',
    'beforeChange .carousel'            : 'loadSlides',
    'afterChange .carousel'             : 'carouselAfterChange',
    'beforeChange .js-related-carousel' : 'exhibitCarouselBeforeChange',
    'click .js-relatedExhibition'       : 'goToExhibition',
    'click .js-item-link'               : 'goToItemPage',
    'click .js-rc-page'                 : 'paginateRelatedCollections',
    'click .js-relatedCollection'       : 'selectRelatedCollection',
    'click .js-disqus'                  : 'initDisqus'
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

  carouselAfterChange: function(e, slick) {
    if (typeof ga !== 'undefined') {
      ga('send', 'event',
        'related content',
        'paginate items',
        $('.carousel__search-results').data('set'));
    }
    if(this.beforeChange) {
      var data_params;
      if (this.addBefore === true) {
        var firstSlide = $($('.js-carousel_item a')[0]);
        data_params = this.model.toJSON();
        data_params.start = Math.max(firstSlide.data('item_number') - this.carouselRows, 0);
        data_params.rows = this.carouselRows;

        // useful output for debugging this bit of code.
            // console.log('item range: ' + $($('.js-carousel_item a')[0]).data('item_number') + ' - ' +
            //   $($('.js-carousel_item a')[$('.js-carousel_item a').length-1]).data('item_number') + ' current slide: ' +
            //   slickInstance.currentSlide + ' current slide item number: ' +
            //   $($('.js-carousel_item a')[slickInstance.currentSlide]).data('item_number') + ' slide count: ' +
            //   slickInstance.slideCount);

        $.ajax({data: data_params, traditional: true, url: '/carousel/', success: (function(that, slickInstance) {
          return function(data) {
            slickInstance.currentSlide = that.carouselRows;
            slickInstance.slickAdd(data, true);
            if (slickInstance.slideCount > that.carouselRows * 5) {
              //Destroy some nodes off the end
              for (var i=0; i<that.carouselRows; i++) {
                slickInstance.slickRemove(slickInstance.slideCount, true);
              }
            }
          };
        }(this, slick))});
        this.addBefore = false;
      }

      if (this.addAfter === true) {
        var lastSlide = $('.js-carousel_item')[$('.js-carousel_item').length - 1];
        data_params = this.model.toJSON();
        data_params.start = $(lastSlide).children('a').data('item_number') + 1;
        data_params.rows = this.carouselRows;

        $.ajax({data: data_params, traditional: true, url: '/carousel/', success: (function(that, slickInstance) {
          return function(data) {
            slickInstance.slickAdd(data);
              // Destroy some nodes off the beginning
              for (var i=0; i<that.carouselRows; i++) {
                slickInstance.currentSlide = slickInstance.currentSlide - 1;
                slickInstance.slickRemove(1, true);
              }
            };
        }(this, slick))});
        this.addAfter = false;
      }
      this.beforeChange = false;
    }
    else {
      // afterChange triggered without beforeChange being triggered
      var numFound = $('#js-carousel').data('numfound');
      if ($('[data-item_number=' + (numFound-1) + ']').length === 1) {
        // if the last item is loaded, assume the user was trying to hit 'next'
        slick.slickGoTo(slick.currentSlide + slick.options.slidesToScroll + 1);
      }
      if ($('[data-item_number=0]').length === 1) {
        // if the first item is loaded, assume the user was trying to hit 'prev'
        slick.slickGoTo(0);
      }
    }
  },

  exhibitCarouselBeforeChange: function() {
    if (typeof ga !== 'undefined') {
      ga('send', 'event',
        'related content',
        'paginate exhibitions',
        $('.carousel__search-results').data('set'));
    }
  },

  goToExhibition: function() {
    if (typeof ga !== 'undefined') {
      ga('send', 'event',
        'related content',
        'select exhibition',
        $('.carousel__search-results').data('set'));
    }
  },

  // `beforeChange` triggered on `.carousel`
  // lazy-loading slides on pagination of the carousel
  loadSlides: function(e, slick, currentSlide, nextSlide) {
    this.beforeChange = true;
    var numLoaded = $('.carousel').slick('getSlick').slideCount;
    var numFound = $('#js-carousel').data('numfound');

    // PREVIOUS BUTTON PRESSED
    if (nextSlide < currentSlide && numLoaded < numFound) {
      if (0 <= nextSlide && nextSlide < this.carouselRows && $('[data-item_number=0]').length === 0) {
        this.addBefore = true;
      }
    }
    // NEXT BUTTON PRESSED
    else if (nextSlide > currentSlide && numLoaded < numFound) {
      var lastItem = numFound-1;
      var remainder = numLoaded-nextSlide-this.carouselRows;

      if (remainder <= this.carouselRows && remainder > 0) {
        if ($('[data-item_number=' + lastItem + ']').length === 0) {
          this.addAfter = true;
        }
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
      if (typeof ga !== 'undefined') {
        ga('send', 'event',
          'related content',
          'select item',
          $('.carousel__search-results').data('set'));
      }

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
  // also called in initialize and pjax_end with e=undefined
  paginateRelatedCollections: function(e) {
    var data_params = this.model.toJSON();
    // don't need carousel specific item data for the related collections
    delete data_params.itemNumber;
    if (e !== undefined) {
      if (typeof ga !== 'undefined') {
        ga('send', 'event',
          'related content',
          'paginate collections',
          $('.carousel__search-results').data('set'));
      }
      data_params.rc_page = $(e.currentTarget).data('rc_page');
    } else {
      if ($('.js-rc-page').length === 2) {
        // stay on the same page when using the carousel to navigate
        // (not sure bug or feature???)
        data_params.rc_page = $($('.js-rc-page')[1]).data('rc_page') - 1;
      } else {
        data_params.rc_page = 0;
      }
    }
    // regular ajax request - we don't need pushState on the url here
    $.ajax({data: data_params, traditional: true, url: '/relatedCollections/', success: function(data) {
        $('#js-relatedCollections').html(data);
      }
    });
  },

  // ultimately this will like get called from a 'click' triggered on paging exhibits
  // as well as the initialize() and pjax_end() functions where it's called now
  // for now most exhibit items really only exist in one exhibit - not so many that 
  // we need pagination
  paginateRelatedExhibitions: function() {
    var params = this.model.toJSON();
    delete params.itemNumber;

    $.ajax({data: params, traditional: true, url: '/relatedExhibitions/', success: function(data) {
        var carouselConfigInit = {
          infinite: false,
          slidesToShow: 4,
          slidesToScroll: 4,
          responsive: [
            {
              breakpoint: 900,
              settings: {
                slidesToShow: 3,
                slidesToScroll: 3
              }
            },
            {
              breakpoint: 650,
              settings: {
                slidesToShow: 2,
                slidesToScroll: 2
              }
            }
          ]
        };
        $('#js-relatedExhibitions').html(data);
        $('.js-related-carousel').show();
        $('.js-related-carousel').slick(carouselConfigInit);
      }
    });
  },

  // `click` triggered on `.js-relatedCollection`
  selectRelatedCollection: function(e) {
    this.model.clear({silent: true});
    if($(e.currentTarget).data('relation') !== undefined) {
      e.preventDefault();
      this.model.set({ relation_ss: [$(e.currentTarget).data('relation')] });
      $.pjax({
        url: $(e.currentTarget).attr('href').split('?')[0],
        container: '#js-pageContent',
        data: this.model.toJSON(),
        traditional: true
      });
    } else {
      if (typeof ga !== 'undefined') {
        ga('send', 'event',
          'related content',
          'select collection',
          $('.carousel__search-results').data('set'));
      }
    }
  },

  // HELPER METHODS
  // --------------------

  // When the width changes, we have to change the carousel's slidesToShow
  // and slidesToScroll options (can't scroll by 8 in mobile mode)
  changeWidth: function() {
    var visibleCarouselWidth = $('#js-carousel .slick-list').prop('offsetWidth');
    var currentSlide = $($('.js-carousel_item')[$('.carousel').slick('slickCurrentSlide')]);
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

    this.carouselRows = numFullThumbs;
    $('.carousel').slick('slickSetOption', 'slidesToShow', numPartialThumbs, false);
    $('.carousel').slick('slickSetOption', 'slidesToScroll', numFullThumbs, true);
  },

  // get the first set of slides for the carousel
  initCarousel: function() {
    var data_params = this.model.toJSON();
    data_params.rows = this.carouselRows*3;
    data_params.start = this.carouselInitStart = Math.max(data_params.itemNumber - this.carouselRows, 0);
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
          var carouselConfigInit = Object.assign(
            {
              initialSlide: Math.min(that.carouselRows, that.model.attributes.itemNumber),
              slidesToShow: that.carouselRows,
              slidesToScroll: that.carouselRows
            },
            that.carouselConfig
          );
          // in more like this, that.model.attributes.itemNumber is undefined
          if(!carouselConfigInit.initialSlide) {
            carouselConfigInit.initialSlide = 0;
          }
          $('#js-carouselContainer').html(data);
          $('.carousel').show();
          $('.carousel').slick(carouselConfigInit);
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
    if(typeof DISQUS !== 'undefined') {
      this.resetDisqus();
    } else {
      $('#disqus_thread').empty();
      var disqus_shortname = $('#disqus_loader').data('disqus');
      $.ajaxSetup({cache:true});
      $.getScript('//' + disqus_shortname + '.disqus.com/embed.js');
      $.ajaxSetup({cache:false});
    }
    $('#disqus_loader').hide();
  },

  resetDisqus: function() {
    $('#disqus_thread').empty();
    DISQUS.reset({
      reload: true,
      config: function() {
        // seems to work to change the shortname for a pre-loaded disqus package
        // despite lack of documentation around this.forum and whether or not it's
        // okay to change from this config function
        this.forum = $('#disqus_loader').data('disqus');
        this.page.url = window.location.href;
      }
    });
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

        if ($('#disqus_thread').length) {
          if ($('#disqus_thread').html().length > 0) {
            that.resetDisqus();
          }
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

      // when navigating between items, the related collections is *not* a part of
      // the #js-itemContainer document document fragment returned, so here we manually 
      // retrieve new related collections
      that.paginateRelatedCollections(undefined);
      that.paginateRelatedExhibitions();

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
    this.paginateRelatedExhibitions();
    this.initMediaPlayer();
    if ($('#disqus_thread').length) {
      if ($('#disqus_thread').html().length > 0) {
        this.resetDisqus();
      }
    }

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
