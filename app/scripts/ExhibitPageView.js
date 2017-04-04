/*global Backbone */
/*exported ExhibitPageView */

'use strict';

// component created if selector in DOM, selector is in the following templates (2017-04-04)
// selector: #js-exhibit-title
// templates: calCultures.html, essayView.html, exhibitView.html, lessonPlanView.html, and themeView.html
// all exhibit-related pages except for the three browse pages (Random Explore, Browse All, and Title Search)

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

  pjax_beforeReplace: function(e) {
    // for navigation away from the exhibit item lightbox via
    // 'go to item page', 'contributing institution' and 'collection' links
    if (e.target !== $('#js-exhibit-item__container')[0] && $('#js-exhibit-item').is(':visible')) {
      $('.modal-backdrop').remove();
      $('body').removeClass('modal-open');
    }
  },

  pjax_beforeSend: function(e, xhr) {
    xhr.setRequestHeader('X-Exhibit-Item', 'true');
  },

  pjax_end: function() {
    if(!($('#js-exhibit-item').is(':visible')) && $('#js-exhibit-item__container').children().length > 0) {
      $('#js-exhibit-item').modal();
    } else if ($('#js-exhibit-item__container').children().length <= 0) {
      $('#js-exhibit-item').modal('hide');
    }
  },

  initialize: function() {
    if ($('#js-exhibit-item__container').children().length > 0) {
      $('#js-exhibit-item').modal();
    }

    $(document).on('pjax:beforeSend', '#js-exhibit-item__container', this.pjax_beforeSend);
    $(document).on('pjax:beforeReplace', '#js-pageContent', this.pjax_beforeReplace);
    $(document).on('pjax:end', '#js-exhibit-item__container', this.pjax_end);
  },

  reset: function() {
    this.initCarousel();
    this.clientTruncate();
  },

  destroy: function() {
    $(document).off('pjax:beforeSend', '#js-exhibit-item__container', this.pjax_beforeSend);
    $(document).off('pjax:beforeReplace', '#js-pageContent', this.pjax_beforeReplace);
    $(document).off('pjax:end', '#js-exhibit-item__container', this.pjax_end);
    this.undelegateEvents();
  }
});
