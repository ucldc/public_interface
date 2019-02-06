/*global Backbone, _ */
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

  // `events: 'submit' '#js-searchForm,#js-footSearch'`   
  // on submit, change the model, don't submit the form
  clearAndSubmit: function(e) {
    this.model.set({q: $(e.currentTarget).find('input[name=q]').val()}, {silent: true});
    this.model.trigger('change:q');
    e.preventDefault();
  },

  // `events: 'click' '.js-global-header__bars-icon'`   
  // Toggle mobile menu with search box:
  toggleMobileMenu: function() {
    $('.js-global-header__search').toggleClass('global-header__search global-header__search--selected');
    if ($('.js-global-header__search').is(':visible')) {
      $('.js-global-header__search').attr('aria-expanded', true);
    } else {
      $('.js-global-header__search').attr('aria-expanded', false);
    }
    $('.js-global-header__mobile-links').toggleClass('.global-header__mobile-links global-header__mobile-links--selected');
    if ($('.js-global-header__mobile-links').is(':visible')) {
      $('.js-global-header__mobile-links').attr('aria-expanded', true);
    } else {
      $('.js-global-header__mobile-links').attr('aria-expanded', false);
    }
  },

  // `events: 'click' '.js-global-header__search-icon'`   
  // Toggle only search box:
  toggleMobileSearch: function() {
    $('.js-global-header__search').toggleClass('global-header__search global-header__search--selected');
    if ($('.js-global-header__search').is(':visible')) {
      $('.js-global-header__search').attr('aria-expanded', true);
    } else {
      $('.js-global-header__search').attr('aria-expanded', false);
    }
  },

  // `events: 'click' '#js-global-header-logo'`   
  // Clear the query manager's current query state
  clearQueryManager: function() {
    if (!_.isEmpty(this.model.attributes)) {
      this.model.clear({silent: true});
    }
  },

  initialize: function() {
    this.listenTo(this.model, 'change:q', this.render);
    $(document).on('pjax:beforeReplace', '#js-pageContent', this.pjax_beforeReplace);
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

