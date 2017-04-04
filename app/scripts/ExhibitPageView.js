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

  // events: {'click .js-exhibit-item': 'exhibitItemView'}
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
  // events: {'hidden.bs.modal #js-exhibit-item': 'exhibitView'}
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
  // events: {'click .js-blockquote': 'showExhibitOverview'}
  showExhibitOverview: function() {
    var isTruncated = $('.js-exhibit__overview').triggerHandler('isTruncated');
    if (isTruncated) {
      $('.js-exhibit__overview').trigger('destroy');
      $('.js-exhibit__overview').css('height', 'auto');
      $('#js-exhibit__overview').text('Read less.');
    }
  },
  // events: {'click #js-exhibit__overview': 'toggleExhibitOverview'}
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
  // events: {'click .js-show-all-exhibit-items': 'togglePrimarySourceSet'}
  togglePrimarySourceSet: function() {
    $('.js-exhibit-items-overflow').slideToggle();
    if ($($('.js-show-all-exhibit-items')[0]).text() === 'View all') {
      $('.js-show-all-exhibit-items').text('View fewer');
    } else {
      $('.js-show-all-exhibit-items').text('View all');
    }
  },
  // events: {'mouseenter .primarysource__link': 'dotDotDot'}
  dotDotDot: function(e) {
    $(e.currentTarget).find('.exhibit__caption').dotdotdot();
  },
  // events: {'mouseleave .primarysource__link': 'killDotDotDot'}
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

  // if an exhibit item is displayed *and* the event target /isn't/ the item container
  // we're leaving the exhibit space and need to remove the modal backdrop before we go
  // ('go to item page', 'contributing institution' and 'collection' links)
  pjax_beforeReplace: function(e) {
    if (e.target !== $('#js-exhibit-item__container')[0] && $('#js-exhibit-item').is(':visible')) {
      $('.modal-backdrop').remove();
      $('body').removeClass('modal-open');
    }
  },

  // this specifies to use the pjax-exhibit-item.html template in the response
  pjax_beforeSend: function(e, xhr) {
    xhr.setRequestHeader('X-Exhibit-Item', 'true');
  },

  // this pjax_end_pageContent is called when the event is triggered for div#js-pageContent
  // so this includes theme pages, lesson plans, exhibit pages, etc. not just item display
  pjax_end: function(that) {
    return function(xhr) {
      // if the part getting replaced is js-exhibit-item__container, do modal stuff
      if (xhr.target.id === 'js-exhibit-item__container') {
        if ($('#js-exhibit-item__container').children().length && !$('#js-exhibit-item').is(':visible')) {
          $('#js-exhibit-item').modal();
        } else if (!$('#js-exhibit-item__container').children().length) {
          $('#js-exhibit-item').modal('hide');
        }
      }

      // if the part getting replaced is the page content (theme pages, lesson plans, exhibit pages, etc.)
      // init carousels and truncate exhibit overview
      if (xhr.target.id === 'js-pageContent') {
        that.initCarousel();
        $('.js-exhibit__overview').dotdotdot();
      }
    };
  },

  initialize: function() {
    if ($('#js-exhibit-item__container').children().length) {
      $('#js-exhibit-item').modal();
    }

    $(document).on('pjax:beforeSend', '#js-exhibit-item__container', this.pjax_beforeSend);
    $(document).on('pjax:beforeReplace', '#js-pageContent', this.pjax_beforeReplace);
    $(document).on('pjax:end', '#js-pageContent', this.pjax_end(this));

    this.initCarousel();
    $('.js-exhibit__overview').dotdotdot();
  },

  destroy: function() {
    $(document).off('pjax:beforeSend', '#js-exhibit-item__container', this.pjax_beforeSend);
    $(document).off('pjax:beforeReplace', '#js-pageContent', this.pjax_beforeReplace);
    $(document).off('pjax:end', '#js-pageContent', this.pjax_end(this));
    this.undelegateEvents();
  }
});
