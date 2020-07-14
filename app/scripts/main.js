'use strict'; // for jshint

/**
 *  @file       main.js
 *
 *  @author     Joel
 *
 *  This is javascript for the static `/app` mockup specs
 * `gulp serve` site -- does not run on django site
 *
 * comments "// amy integrated" means version in `search.js`
 *
 **/

// ##### Global Header ##### //

var navOpenState;
var searchOpenState;

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

$(document).ready(function(){

  // Remove 'no-jquery' class from <html> element if jquery loads properly:
	// amy integrated
  $('html').removeClass('no-jquery');

  // ##### Search Filters ##### //

  // Show more filters
  $('.js-filter__more-link').click(function(){
    $('.js-filter__more').addClass('filter__more--show').removeClass('filter__more');
    $('.js-filter__more-link').addClass('filter__more-link--hide').removeClass('filter__more-link');
  });

  // Show less filters
  $('.js-filter__less-link').click(function(){
    $('.js-filter__more').addClass('filter__more').removeClass('filter__more--show');
    $('.js-filter__more-link').addClass('filter__more-link').removeClass('filter__more-link--hide');
  });

  // ##### Checkbox Groups ##### //

  // Disable Update Results button upon document.ready
	// amy integrated
  $('.js-a-check__update').prop('disabled', true);

  // Expand checkbox group and switch arrow icon when clicking on header (small and medium screens):
	// amy integrated
  $('.js-a-check__header').click(function(){
    $(this).next('.js-a-check__popdown').toggleClass('check__popdown check__popdown--selected');
    $(this).children('.js-a-check__header-arrow-icon').toggleClass('fa-angle-down fa-angle-up');
  });

  // Select all or deselect all checkboxes (small and medium screens):
	// amy integrated
  $('.js-a-check__button-select-all').click(function(){
    $('.check__input').prop('checked', true);
    $('.js-a-check__button-deselect-all').prop('disabled', false);
    $('.js-a-check__update').prop('disabled', false);
  });
  $('.js-a-check__button-deselect-all').click(function(){
    $('.check__input').prop('checked', false);
    $('.js-a-check__update').prop('disabled', false);
  });

  // Select all or deselect all checkboxes (large screens):
	// amy integrated
  $('.js-a-check__link-select-all').click(function(){
    $('.check__input').prop('checked', true);
    $('.js-a-check__link-deselect-all').toggleClass('check__link-deselect-all--not-selected check__link-deselect-all--selected');
    $('.js-a-check__link-select-all').toggleClass('check__link-select-all--selected check__link-select-all--not-selected');
    $('.js-a-check__button-deselect-all').prop('disabled', false);
    $('.js-a-check__update').prop('disabled', false);
  });
  $('.js-a-check__link-deselect-all').click(function(){
    $('.check__input').prop('checked', false);
    $('.js-a-check__link-deselect-all').toggleClass('check__link-deselect-all--selected check__link-deselect-all--not-selected');
  	$('.js-a-check__link-select-all').toggleClass('check__link-select-all--not-selected check__link-select-all--selected');
  	$('.js-a-check__update').prop('disabled', false);
  });

  // If a checkbox is already checked, enable Deselect All button:
	// amy integrated
  if ($('.check__input').is(':checked')) {
  	$('.js-a-check__button-deselect-all').prop('disabled', false);
  }

  // If a new checkbox is checked, enable Deselect All button and enable Update Results button:
	// amy integrated
  $('.check__input').change(function(){
    if ($('.check__input').is(':checked')) {
  		$('.js-a-check__button-deselect-all').prop('disabled', false);
  	}
  $('.js-a-check__update').prop('disabled', false);
  });

  // Collapse checkbox group, disable Update Results button, and change header styles if any checkboxes are already checked:
	// amy integrated
  $('.js-a-check__update').click(function(){
    $('.js-a-check__update').prop('disabled', true);
  	$('.js-a-check__popdown').toggleClass('check__popdown check__popdown--selected');
    $('.js-a-check__header-arrow-icon').toggleClass('fa-angle-up fa-angle-down');
    if ($('.check__input').is(':checked')) {
  		$('.js-a-check__header').addClass('check__header--selected').removeClass('check__header');
  		$('.js-a-check__header-text').addClass('check__header-text--selected').removeClass('check__header-text');
    } else {
      $('.js-a-check__header').removeClass('check__header--selected').addClass('check__header');
      $('.js-a-check__header-text').removeClass('check__header-text--selected').addClass('check__header-text');
  	}
  });

  // amy integrated
  $('.js-obj__osd-infobanner-link').click(function(){
    $('.js-obj__osd-infobanner').slideUp('fast');
  });

}); // End of $(document).ready(function()

// ##### Tooltip ##### //

// amy integrated
$('[data-toggle="tooltip"]').tooltip({
  placement: 'top'
});

// Detect background-blend-mode css property in browser and, if not available, write class to html element
// amy integrated
if(!('backgroundBlendMode' in document.body.style)) {
    // No support for background-blend-mode
  var html = document.getElementsByTagName('html')[0];
  html.className = html.className + ' no-background-blend-mode';
}

// ##### Slick Carousel ##### //
// amy integrated
$('.carousel').show();
$('.carousel').slick({
  infinite: false,
  speed: 300,
  slidesToShow: 10,
  slidesToScroll: 6,
  variableWidth: true,
  lazyLoad: 'ondemand',
  responsive: [
    {
      breakpoint: 1200,
      settings: {
        infinite: true,
        // slidesToShow: 8,
        slidesToScroll: 8,
        variableWidth: true
      }
    },
    {
      breakpoint: 900,
      settings: {
        infinite: true,
        // slidesToShow: 6,
        slidesToScroll: 6,
        variableWidth: true
      }
    },
    {
      breakpoint: 650,
      settings: {
        infinite: true,
        // slidesToShow: 4,
        slidesToScroll: 4,
        variableWidth: true
      }
    }
  ]
});

// ***** Complex Carousel ***** //
// amy integrated
$('.carousel-complex').show();
$('.carousel-complex__item-container').slick({
  infinite: false,
  speed: 300,
  slidesToShow: 6,
  slidesToScroll: 6,
  variableWidth: true,
  lazyLoad: 'ondemand',
  responsive: [
    {
      breakpoint: 1200,
      settings: {
        infinite: true,
        // slidesToShow: 8,
        slidesToScroll: 8,
        variableWidth: true
      }
    },
    {
      breakpoint: 900,
      settings: {
        infinite: true,
        // slidesToShow: 6,
        slidesToScroll: 6,
        variableWidth: true
      }
    },
    {
      breakpoint: 650,
      settings: {
        infinite: true,
        // slidesToShow: 4,
        slidesToScroll: 4,
        variableWidth: true
      }
    }
  ]
});

// ***** jQuery.dotdotdot ***** //

$(document).ready(function() {
  $('.obj__heading').dotdotdot({
    ellipsis: '…',
    watch: 'window',
    height: 50,
    lastCharacter: { // remove these characters from the end of the truncated text:
      remove: [ ' ', ',', ';', '.', '!', '?', '[', ']' ]
    }
  });
  $('.thumbnail__caption').dotdotdot({
    ellipsis: '…',
    watch: 'window',
    height: 30,
    lastCharacter: {
      remove: [ ' ', ',', ';', '.', '!', '?', '[', ']' ]
    }
  });
  $('.carousel__thumbnail-caption').dotdotdot({
    ellipsis: '…',
    watch: 'window',
    height: 30,
    lastCharacter: {
      remove: [ ' ', ',', ';', '.', '!', '?', '[', ']' ]
    }
  });
});

// Alternative JavaScript method (instead of CSS method) for disabling popover via breakpoint:
// if (Modernizr.mq('only screen and (max-width: 800px)')) {
//  $('.popover__link').popover('destroy');
// }
