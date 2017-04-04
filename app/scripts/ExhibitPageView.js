/*global Backbone */
/*exported ExhibitPageView */

'use strict';

var ExhibitPageView = Backbone.View.extend({
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

  reset: function() {
    this.initCarousel();
    this.clientTruncate();
  },

  destroy: function() {
    this.undelegateEvents();
  }
});
