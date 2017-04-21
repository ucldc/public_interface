/*global Backbone, _ */
/*exported ContactOwnerFormView */

'use strict';

var ContactOwnerFormView = Backbone.View.extend({
  el: $('#js-contactOwner'),
  events: {
    'change #contactOwner-requestReason'    : 'updateSubject',
    'submit'                                : 'submitForm',
    'blur #contactOwner-verifyEmail'        : 'verifyEmail',
    'change #contactOwner-demographic'      : 'otherEditable'
  },

  updateSubject: function(e) {
    $('.js-requestReason').text($(e.currentTarget).val());
  },
  
  verifyEmail: function(e) {
    var el = $(e.currentTarget);
    if (el.val() !== $('#contactOwner-email').val()) {
      if (!(el.parent().hasClass('has-error'))) {
        el.parent().addClass('has-error');
        $(el.siblings('label')[0]).text('Verify Email: Your emails do no match.');
        $('#contactOwner-submit').prop('disabled', true);
      }
    } else {
      if ((el.parent().hasClass('has-error'))) {
        el.parent().removeClass('has-error');
        $(el.siblings('label')[0]).text('Verify Email:');
        $('#contactOwner-submit').prop('disabled', false);
      }
    }
  },
  
  otherEditable: function(e) {
    if ($(e.currentTarget).val() === 'other') {
      $('#contactOwner-speicifedDemographic').prop('disabled', false);
    } else {
      $('#contactOwner-speicifedDemographic').val('');
      $('#contactOwner-speicifedDemographic').prop('disabled', true);
    }
  },

  submitForm: function(e) {
    e.preventDefault();
    var formSubmission = $('#js-contactOwner').serializeArray();
    var submitForm = true;
    
    if($('#contactOwner-email').val() !== $('#contactOwner-verifyEmail').val()) {
      if (!($('#contactOwner-verifyEmail').parent().hasClass('has-error'))) {
        $('#contactOwner-verifyEmail').parent().addClass('has-error');
        $($('#contactOwner-verifyEmail').siblings('label')[0]).text('Verify Email: Your emails do no match.');
        $('#contactOwner-submit').prop('disabled', true);
      }
      submitForm = false;
    }
    
    _.each(formSubmission, function(element) {
      if(_.isEmpty(element.value)) {
        submitForm = false;
        $('[form=js-contactOwner][name=' + element.name + ']').parent().addClass('has-error');
      } else {
        if ($('[form=js-contactOwner][name=' + element.name + ']').parent().hasClass('has-error')) {
          $('[form=js-contactOwner][name=' + element.name + ']').parent().removeClass('has-error');
        }
      }
    });
    
    if (submitForm) {
      $.ajax({
        url: $(e.currentTarget).attr('action'),
        data: formSubmission,
        traditional: true, 
        success: function(data) {
          $('#js-contactOwnerForm').html(data);
        }
      });      
    }
  }
});