/*global _*/
'use strict';

$(document).ready(function() {
  if ($('.home').length) {
    _.each($('form'), function(el) {
      el.reset();
    });

    $(document).on('click', '.js-global-header__bars-icon', function() {
      $('.js-global-header__search').toggleClass('.global-header__search global-header__search--selected');
      $('.js-global-header__mobile-links').toggleClass('.global-header__mobile-links global-header__mobile-links--selected');
      if ($('.js-global-header__mobile-links').is(':visible')) {
        $('.js-global-header__mobile-links').attr('aria-expanded', true);
      } else {
        $('.js-global-header__mobile-links').attr('aria-expanded', false);
      }
    });

    // Toggle only search box:
    //  $('.js-global-header__search-icon').click(function(){
    $(document).on('click', '.js-global-header__search-icon', function() {
      $('.js-global-header__search').toggleClass('global-header__search global-header__search--selected');
    });
  }
});