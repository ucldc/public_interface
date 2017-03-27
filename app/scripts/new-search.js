/*global Backbone, _, ContactOwnerForm, OpenSeadragon, tileSources, imagesLoaded */
/*exported GlobalSearchForm, FacetForm, CarouselContext, ComplexCarousel */

'use strict';

var exhibitPage = Backbone.View.extend({
  el: $('#js-pageContent'),
  events: {
    'click .js-exhibit-item'            : 'exhibitItemView',
    'hidden.bs.modal #js-exhibit-item'  : 'exhibitView',
    'click .js-blockquote'              : 'showExhibitOverview',
    'click #js-exhibit__overview'       : 'toggleExhibitOverview',
    'click .js-show-all-exhibit-items'  : 'togglePrimarySourceSet',
    'mouseenter .primarysource__link'   : 'dotDotDot',
    'mouseleave .primarysource__link'   : 'killDotDotDot',
  },
  exhibitItemView: function(e) {
    // Middle click, cmd click, and ctrl click should open
    // links in a new tab as normal.
    if ( e.which > 1 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey ) { return; }
    e.preventDefault();
    $.pjax({
      push: true,
      scrollTo: false,
      url: $(e.currentTarget).attr('href'),
      container: '#js-exhibit-item__container'
    });
  },

  exhibitView: function() {
    if ($('#js-exhibit-item__container').children().length > 0) {
      $.pjax({
        push: true,
        scrollTo: false,
        url: $('#js-exhibit-item .close').data('url'),
        container: '#js-exhibit-item__container'
      });
    }
  },

  showExhibitOverview: function() {
    var isTruncated = $('.js-exhibit__overview').triggerHandler('isTruncated');
    if (isTruncated) {
      $('.js-exhibit__overview').trigger('destroy');
      $('.js-exhibit__overview').css('height', 'auto');
      $('#js-exhibit__overview').text('Read less.');
    }
  },

  toggleExhibitOverview: function() {
    var isTruncated = $('.js-exhibit__overview').triggerHandler('isTruncated');

    if (isTruncated) {
      $('.js-exhibit__overview').trigger('destroy');
      $('.js-exhibit__overview').css('height', 'auto');
      $('#js-exhibit__overview').text('Read less.');
    }
    else {
      $('.js-exhibit__overview').css('height', '400px').dotdotdot();
      $('#js-exhibit__overview').text('Read full exhibition overview.');
    }
  },

  togglePrimarySourceSet: function() {
    $('.js-exhibit-items-overflow').slideToggle();
    if ($($('.js-show-all-exhibit-items')[0]).text() === 'View all') {
      $('.js-show-all-exhibit-items').text('View fewer');
    } else {
      $('.js-show-all-exhibit-items').text('View all');
    }
  },

  dotDotDot: function(e) {
    $(e.currentTarget).find('.exhibit__caption').dotdotdot();
  },

  killDotDotDot: function(e) {
    $(e.currentTarget).find('.exhibit__caption').trigger('destroy');
  },

  initCarousel: function() {
    $('.js-related-carousel').slick({
      infinite: false,
      slidesToShow: 4,
      slidesToScroll: 1,
      responsive: [
        {
          breakpoint: 900,
          settings: {
            slidesToShow: 3
          }
        },
        {
          breakpoint: 650,
          settings: {
            slidesToShow: 2
          }
        }
      ]
    });
  },

  clientTruncate: function() {
    $('.js-exhibit__overview').dotdotdot();
  },

  initialize: function() {
    if ($('#js-exhibit-item__container').children().length > 0) {
      $('#js-exhibit-item').modal();
    }
  },
});

var FacetForm = Backbone.View.extend({
  el: $('#js-pageContent'),
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

  setRefineQuery: function(e) {
    this.model.set({start: 0, rq: $.map($('input[name=rq]'), function(el) { return $(el).val(); })});
    e.preventDefault();
  },
  removeRefineQuery: function(e) {
    var txtFilter = $(e.currentTarget).data('slug');
    $('input[form="js-facet"][name="rq"][value="' + txtFilter + '"]').val('');
    this.model.set({start: 0, rq: _.without(this.model.get('rq'), txtFilter)});
  },
  setFacet: function(e) {
    var filterType = $(e.currentTarget).attr('name');
    var attributes = {start: 0};
    attributes[filterType] = $.map($('input[name=' + filterType + ']:checked'), function(el) { return $(el).val(); });
    this.model.set(attributes);
  },
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
  toggleViewFormat: function(e) {
    var viewFormat = $(e.currentTarget).attr('id');
    $('#view_format').prop('value', viewFormat);
    this.model.set({view_format: viewFormat});
  },
  setSort: function(e) {
    this.model.set({start: 0, sort: $(e.currentTarget).val() });
  },
  setRows: function(e) {
    this.model.set({start: 0, rows: $(e.currentTarget).val() });
  },
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

  deselectAll: function(e) { this.selectDeselectAll(e, false); },
  selectAll: function(e) { this.selectDeselectAll(e, true); },
  selectDeselectAll: function(e, checked) {
    var filterElements = $(e.currentTarget).parents('.check').find('.js-facet');
    filterElements.prop('checked', checked);
    filterElements.trigger('change');
    e.preventDefault();
  },
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
  clearFilters: function() {
    var filterElements = $('.js-facet');
    filterElements.prop('checked', false);
    filterElements.trigger('change');
  },

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
  updateFacets: function(e) {
    e.preventDefault();
    this.facetSearch();
  },
  facetSearch: function() {
    $.pjax({
      url: $('#js-facet').attr('action'),
      container: '#js-pageContent',
      data: this.model.toJSON(),
      traditional: true
    });
  },

  paginateRelatedCollections: function(e) {
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
    //TODO: function(data, status, jqXHR)
    $.ajax({data: data_params, traditional: true, url: '/relatedCollections/', success: function(data) {
        $('#js-relatedCollections').html(data);
      }
    });
  },

  goToCollectionPage: function() {
    this.model.clear({silent: true});
  },

  changeWidth: function(window_width) {
    if (window_width > 900) { this.desktop = true; }
    else { this.desktop = false; }
  },

  render: function() {
    if(!_.isEmpty(this.model.changed) && !_.has(this.model.changed, 'q')) {
      if(this.desktop) {
        this.facetSearch();
      }
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
        if (attrUndefined) {
          this.facetSearch();
        }
        _.each(this.model.changed, function(value, key) {
          if (key === 'type_ss' || key === 'facet_decade' || key === 'repository_data' || key === 'collection_data') {
            $('.facet-' + key).parents('.check').find('.js-a-check__update').prop('disabled', false);
          }
        });
      } else {
        this.facetSearch();
      }
    }
  },

  initialize: function() {
    this.listenTo(this.model, 'change', this.render);
    this.changeWidth($(window).width());
  }
});

var CarouselContext = Backbone.View.extend({
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
    // Middle click, cmd click, and ctrl click should open
    // links in a new tab as normal.
    if ( e.which > 1 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey ) { return; }

    this.model.unset('itemId', {silent: true});
    this.model.unset('itemNumber', {silent: true});

    if (this.model.get('referral') !== undefined) {
      if (this.model.get('referral') === 'institution') {
        this.model.unset('repository_data', {silent: true});
      } else if (this.model.get('referral') === 'campus') {
        this.model.unset('campus_slug', {silent: true});
      } else if (this.model.get('referral') === 'collection') {
        this.model.unset('collection_data', {silent: true});
      }
      this.model.unset('referral', {silent: true});
      this.model.unset('referralName', {silent: true});
    }

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
    if ((currentSlide > nextSlide && (nextSlide !== 0 || currentSlide === slidesToScroll)) || (currentSlide === 0 && nextSlide > slick.slideCount - slidesToScroll && nextSlide < slick.slideCount)) {
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
  }
});

var ComplexCarousel = Backbone.View.extend({
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
    } else if ($('.carousel-complex__tile--selected').length > 0) {
      $('.carousel-complex__item-container').slick('slickGoTo', $('.carousel-complex__tile--selected').data('slick-index'));
    }
  },

  initialize: function() {
    this.initCarousel();
    imagesLoaded('.carousel-complex__item-container img', (function(that) {
      return function() {
        that.changeWidth();
      };
    }(this)));
  }
});

var GlobalSearchForm = Backbone.View.extend({
  el: $('body'),
  events: {
    'submit #js-searchForm,#js-footSearch':     'clearAndSubmit',
    'click .js-global-header__bars-icon':       'toggleMobileMenu',
    'click .js-global-header__search-icon':     'toggleMobileSearch',
    'click #js-global-header-logo':             'clearQueryManager'
  },

  // events: {'submit #js-searchForm,#js-footSearch': 'clearAndSubmit'}
  // on submit, change the model, don't submit the form
  clearAndSubmit: function(e) {
    this.model.set({q: $(e.currentTarget).find('input[name=q]').val()}, {silent: true});
    this.model.trigger('change:q');
    e.preventDefault();
  },

  // events: {'click .js-global-header__bars-icon': 'toggleMobileMenu'}
  // Toggle mobile menu with search box:
  toggleMobileMenu: function() {
    $('.js-global-header__search').toggleClass('global-header__search global-header__search--selected');
    $('.js-global-header__mobile-links').toggleClass('.global-header__mobile-links global-header__mobile-links--selected');
  },

  // events: {'click .js-global-header__search-icon': 'toggleMobileSearch'}
  // Toggle only search box:
  toggleMobileSearch: function() {
    $('.js-global-header__search').toggleClass('global-header__search global-header__search--selected');
  },

  clearQueryManager: function() {
    if (!_.isEmpty(this.model.attributes) || !_.isEmpty(sessionStorage)) {
      this.model.clear({silent: true});
    }
  },

  initialize: function() {
    this.listenTo(this.model, 'change:q', this.render);
  },

  // for use in pjax
  closeMenu: function() {
    $('.js-global-header__search').addClass('global-header__search');
    $('.js-global-header__search').removeClass('global-header__search--selected');
    $('.js-global-header__mobile-links').addClass('global-header__mobile-links');
    $('.js-global-header__mobile-links').removeClass('global-header__mobile-links--selected');
  },

  render: function() {
    if(this.model.has('q')) {
      //get rid of all other search parameters
      var q = this.model.get('q');
      this.model.clear({silent: true});
      this.model.set({q: q}, {silent: true});
      //perform the search!
      $.pjax({
        url: $('#js-searchForm').attr('action'),
        container: '#js-pageContent',
        data: this.model.toJSON()
      });
    } else {
      this.model.clear({silent: true});
      $.pjax({
        url: $('#js-searchForm').attr('action'),
        container: '#js-pageContent',
        data: {'q': ''}
      });
    }

    _.each($('#js-searchForm, #js-footerSearch'), (function(model) {
      return function(form) {
        $('input[name=q][form=' + $(form).attr('id') + ']').val(model.get('q'));
      };
    }(this.model)));
  },

  setupComponents: function() {
    if ($('#js-facet').length > 0) {
      if (this.facetForm === undefined) { this.facetForm = new FacetForm({model: this.model}); }
      this.facetForm.toggleSelectDeselectAll();
      this.facetForm.toggleTooltips();
    }
    else if (this.facetForm !== undefined) {
      this.facetForm.stopListening();
      this.facetForm.undelegateEvents();
      delete this.facetForm;
    }

    if($('#js-carouselContainer').length > 0) {
      if (this.carousel === undefined) { this.carousel = new CarouselContext({model: this.model}); }
    }
    else if (this.carousel !== undefined) {
      this.carousel.undelegateEvents();
      delete this.carousel;
    }

    if($('#js-contactOwner').length > 0) {
      if (this.contactOwnerForm === undefined) { this.contactOwnerForm = new ContactOwnerForm(); }
    }
    else if (this.contactOwnerForm !== undefined) { delete this.contactOwnerForm; }

    if($('.carousel-complex').length > 0) {
      if (this.complexCarousel === undefined) {
        this.complexCarousel = new ComplexCarousel({model: this.model});
        $('.js-obj__osd-infobanner').show();
      }
      else {
        $('.js-obj__osd-infobanner').hide();
        this.complexCarousel.initialize();
      }
      //TODO: this should only have to happen once!
      $('.js-obj__osd-infobanner-link').click(function(){
        $('.js-obj__osd-infobanner').slideUp('fast');
      });
    }
    else if (this.complexCarousel !== undefined) {
      this.complexCarousel.undelegateEvents();
      delete this.complexCarousel;
    }

    if($('#obj__osd').length > 0) {
      if (this.viewer !== undefined) {
        this.viewer.destroy();
        delete this.viewer;
        $('#obj__osd').empty();
      }
      if ($('.openseadragon-container').length > 0) { $('.openseadragon-container').remove(); }
      this.viewer = new OpenSeadragon({
        id: 'obj__osd',
        tileSources: [tileSources],
        zoomInButton: 'obj__osd-button-zoom-in',
        zoomOutButton: 'obj__osd-button-zoom-out',
        homeButton: 'obj__osd-button-home',
        fullPageButton: 'obj__osd-button-fullscreen'
      });
    }
    else if (this.viewer !== undefined) {
      this.viewer.destroy();
      delete this.viewer;
    }

    if($('#js-exhibit-title').length > 0) {
      if (this.exhibitPage === undefined) { this.exhibitPage = new exhibitPage(); }
      this.exhibitPage.initCarousel();
      this.exhibitPage.clientTruncate();
    }
    else if (this.exhibitPage !== undefined) {
      this.exhibitPage.undelegateEvents();
      delete this.exhibitPage;
    }

    if($('#js-exhibit-wrapper').length > 0) {
      this.grid = $('#js-exhibit-wrapper').isotope({
        layoutMode: 'masonry',
        itemSelector: '.js-grid-item',
        percentPosition: true,
        masonry: {
          columnWidth: '.js-grid-sizer'
        }
      });
    }

  },

  changeWidth: function(window_width) {
    if (this.facetForm !== undefined) { this.facetForm.changeWidth(window_width); }
    if (this.carousel !== undefined) { this.carousel.changeWidth(window_width); }
    if (this.complexCarousel !== undefined) { this.complexCarousel.changeWidth(window_width); }
  },

  pjax_beforeReplace: function() {
    if($('#js-mosaicContainer').length > 0) {
      $('#js-mosaicContainer').infinitescroll('destroy');
    }

  },
  pjax_end: function() {
    this.closeMenu();
  }
});

