/*global _*/
'use strict';

function setAttrs (headerElState, headerEl, headerElButton) {
  if (headerElState === false) {
    headerEl.classList.add('is-closed');
    headerEl.classList.remove('is-open');
    headerElButton.setAttribute('aria-expanded', false);
  } else {
    headerEl.classList.add('is-open');
    headerEl.classList.remove('is-closed');
    headerElButton.setAttribute('aria-expanded', true);
  }
}

function watchHeaderWidth (headerWidth) {
  var mobileSearch = document.querySelector('.header__search');
  var mobileSearchButton = document.querySelector('.header__mobile-search-button');
  var mobileNav = document.querySelector('.header__nav');
  var mobileNavButton = document.querySelector('.header__mobile-nav-button');

  if (headerWidth.matches) {
    navOpenState = true;
    searchOpenState = true;
  } else {
    navOpenState = false;
    searchOpenState = false;
  }

  if (mobileSearch) {
    setAttrs(searchOpenState, mobileSearch, mobileSearchButton);
  }
  setAttrs(navOpenState, mobileNav, mobileNavButton);
}


$(document).ready(function() {
  if ($('.home').length) {
    _.each($('form'), function(el) {
      el.reset();
    });

    var navOpenState;
    var searchOpenState;


    if (document.querySelector('.header')) {
      var mobileNavButton = document.querySelector('.header__mobile-nav-button');
      mobileNavButton.addEventListener('click', function (e) {
        var mobileNav = document.querySelector('.header__nav');

        if (navOpenState === true) {
          navOpenState = false;
        } else {
          navOpenState = true;
        }
        setAttrs(navOpenState, mobileNav, e.currentTarget);
      });

      var mobileSearchButton = document.querySelector('.header__mobile-search-button');
      if (mobileSearchButton) {
        mobileSearchButton.addEventListener('click', function (e) {
          var mobileSearch = document.querySelector('.header__search');
          if (searchOpenState === true) {
            searchOpenState = false;
          } else {
            searchOpenState = true;
          }
          setAttrs(searchOpenState, mobileSearch, e.currentTarget);
        });
      }

      var headerWidth = window.matchMedia('(min-width: 650px)');
      // Watch screen width and update nav/search open states:
      watchHeaderWidth(headerWidth);
      headerWidth.addListener(watchHeaderWidth);
    }
  }
});