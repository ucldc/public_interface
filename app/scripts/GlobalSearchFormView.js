/*global Backbone, _, ContactOwnerFormView, OpenSeadragon, tileSources, ExhibitPageView, FacetFormView, CarouselView, ComplexCarouselView */
/*exported GlobalSearchFormView */

'use strict';

var GlobalSearchFormView = Backbone.View.extend({
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
      if (this.facetForm === undefined) { this.facetForm = new FacetFormView({model: this.model}); }
      this.facetForm.toggleSelectDeselectAll();
      this.facetForm.toggleTooltips();
    }
    else if (this.facetForm !== undefined) {
      this.facetForm.stopListening();
      this.facetForm.undelegateEvents();
      delete this.facetForm;
    }

    if($('#js-carouselContainer').length > 0) {
      if (this.carousel === undefined) { this.carousel = new CarouselView({model: this.model}); }
    }
    else if (this.carousel !== undefined) {
      this.carousel.undelegateEvents();
      delete this.carousel;
    }

    if($('#js-contactOwner').length > 0) {
      if (this.contactOwnerForm === undefined) { this.contactOwnerForm = new ContactOwnerFormView(); }
    }
    else if (this.contactOwnerForm !== undefined) { delete this.contactOwnerForm; }

    if($('.carousel-complex').length > 0) {
      if (this.complexCarousel === undefined) {
        this.complexCarousel = new ComplexCarouselView({model: this.model});
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
      if (this.exhibitPage === undefined) { this.exhibitPage = new ExhibitPageView(); }
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

