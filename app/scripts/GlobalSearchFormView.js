/*global Backbone, _ */
/*exported GlobalSearchFormView */

'use strict';

var GlobalSearchFormView = Backbone.View.extend({
  el: $('body'),
  events: {
    'submit #js-searchForm,#js-footSearch':     'clearAndSubmit',
    'click .header__mobile-nav-button':         'toggleMobileMenu',
    'click .header__mobile-search-button':      'toggleMobileSearch',
    'click .js-global-header-logo':             'clearQueryManager'
  },
  navOpenState: true,
  searchOpenState: true,

  // `events: 'submit' '#js-searchForm,#js-footSearch'`   
  // on submit, change the model, don't submit the form
  clearAndSubmit: function(e) {
    this.model.set({q: $(e.currentTarget).find('input[name=q]').val()}, {silent: true});
    this.model.trigger('change:q');
    e.preventDefault();
  },

  // toggles attributes for the header bar
  // (headerElState is always True for desktop/tablet)
  setAttrs: function(headerElState, headerEl, headerElButton) {
    if (headerElState === false) {
      headerEl.classList.add('is-closed');
      headerEl.classList.remove('is-open');
      headerElButton.setAttribute('aria-expanded', false);
    } else {
      headerEl.classList.add('is-open');
      headerEl.classList.remove('is-closed');
      headerElButton.setAttribute('aria-expanded', true);
    }
  },

  // event handler bound in initialize function using native JS
  // the events dictionary used for all other callback functions 
  // automagically wraps callbacks such that 'this' references GlobalSearchFormView
  // in this case, since we're binding via native JS, we have to pass 'that'
  // into the event handler to access the GlobalSearchFormView
  // makes use of window.matchMedia native JS feature
  watchHeaderWidth: function(that) {
    return function(headerWidth) {
      var mobileSearch = document.querySelector('.header__search');
      var mobileSearchButton = document.querySelector('.header__mobile-search-button');
      var mobileNav = document.querySelector('.header__nav');
      var mobileNavButton = document.querySelector('.header__mobile-nav-button');

      if (headerWidth.matches) {
        that.navOpenState = true;
        that.searchOpenState = true;
      } else {
        that.navOpenState = false;
        that.searchOpenState = false;
      }
      if (mobileSearch) {
        that.setAttrs(that.searchOpenState, mobileSearch, mobileSearchButton);
      }
      that.setAttrs(that.navOpenState, mobileNav, mobileNavButton);
    };
  },

  // `events: 'click' '.header__mobile-nav-button'`
  // Toggle mobile menu with search box:
  toggleMobileMenu: function(e) {
    var mobileNav = document.querySelector('.header__nav');

    if (this.navOpenState === true) {
      this.navOpenState = false;
    } else {
      this.navOpenState = true;
    }
    this.setAttrs(this.navOpenState, mobileNav, e.currentTarget);
  },

  // `events: 'click' '.header__mobile-search-button'`
  // Toggle only search box:
  toggleMobileSearch: function(e) {
    var mobileSearch = document.querySelector('.header__search');

    if (this.searchOpenState === true) {
      this.searchOpenState = false;
    } else {
      this.searchOpenState = true;
    }
    this.setAttrs(this.searchOpenState, mobileSearch, e.currentTarget);
  },

  // `events: 'click' '.js-global-header-logo'`   
  // Clear the query manager's current query state
  clearQueryManager: function() {
    if (!_.isEmpty(this.model.attributes)) {
      this.model.clear({silent: true});
    }
  },

  initialize: function() {
    this.listenTo(this.model, 'change:q', this.render);
    $(document).on('pjax:beforeReplace', '#js-pageContent', this.pjax_beforeReplace);

    var headerWidth = window.matchMedia('(min-width: 650px)');
    this.watchHeaderWidth(this)(headerWidth);
    headerWidth.addListener(this.watchHeaderWidth(this));
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

  changeWidth: function(window_width) {
    if (this.facetForm !== undefined) { this.facetForm.changeWidth(window_width); }
    if (this.carousel !== undefined) { this.carousel.changeWidth(window_width); }
    if (this.complexCarousel !== undefined) { this.complexCarousel.changeWidth(window_width); }
  },

  pjax_beforeReplace: function() {
    if($('#js-mosaicContainer').length > 0 && $('#js-collectionPagination').children().length) {
      $('#js-mosaicContainer').infiniteScroll('destroy');
    }

  },
  pjax_end: function() {
    this.closeMenu();
  }
});

