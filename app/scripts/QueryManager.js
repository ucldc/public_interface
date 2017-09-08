/*global Backbone */
/*global _ */
/*exported QueryManager */

'use strict';

// The Query parameters are stored in three places: the DOM, Session Storage, 
// and the JavaScript. Typically the DOM is most correct - having returned from 
// the server. The JavaScript keeps track of things while waiting for a server
// response. Session storage really only matters if pjax breaks. When the full
// page comes back, the JavaScript can pick right back up with the current context
// via session storage. 

// The Query Manager manages two distinct types of query data which are related
// but distinct. There is the general query information: `q`, `rq` (refine query), `view_format`,
// `sort`, `relevance`, `rows`, `start`, `type_of_work`, `decade`, `collection_data`,
// `repository_data` and there is also the item-specific query information: `itemId`, 
// `itemNumber` (where the item falls in the results set - used to calculate the 
// 'start' offset for the carousel), `referral`, and `referralName` 

var QueryManager = Backbone.Model.extend({
  
  defaultValues: {
    /* q: '', */
    rq: '',
    view_format: 'thumbnails',
    sort: 'relevance', 
    rows: '24',
    start: 0
  },
  
  getQueryFromDOM: function(formName) {
    var formSelector = '[form=' + formName + ']';

    if ($(formSelector).length > 0) {
      // $.extend({}) automatically removes undefined values
      var queryObj = $.extend({}, {
        q: $(formSelector + '[name=q]').val(),
        view_format: $(formSelector + '[name=view_format]').val(),
        sort: $(formSelector + '[name=sort]').val(),
        rows: $(formSelector + '[name=rows]').val(),
        start: $(formSelector + '[name=start]').val(),
      });
      if (queryObj.start) { queryObj.start = parseInt(queryObj.start); }

      // :visible differentiates between actual filters and implied filters,
      // such as collection_data on a collection page (stored in an <input hidden class=js-facet> elem)
      var filters;
      if (formName === 'js-facet') {
        filters = $(formSelector + '.js-facet:visible').serializeArray();
      } else {
        filters = $(formSelector + '.js-filter').serializeArray();
      }
      if (filters.length > 0) {
        for (var i=0; i<filters.length; i++) {
          var filter = filters[i];
          //if attributes has key of this filter type
          if (_.has(queryObj, filter.name)) {
            queryObj[filter.name].push(filter.value);
          } else {
            queryObj[filter.name] = [filter.value];
          }
        }
      }
      var refineArray = $(formSelector + '[name=rq]').serializeArray();
      if (refineArray.length > 0) {
        queryObj.rq = [];
        for (var j=0; j<refineArray.length; j++) {
          if (refineArray[j].value !== '') {
            queryObj.rq.push(refineArray[j].value);
          }
        }
      }

      // this causes any previously defined facet values
      // to be wiped out. (see l-120 of this file)
      queryObj = _.defaults(queryObj, {type_ss: '', facet_decade: '', repository_data: '', collection_data: '', rq: ''});
      return queryObj;
    } else {
      console.log('[ERROR]: QueryManager attempting to retrieve query parameters from ' + formName + ' form when no form is in DOM.');
      return {};
    }
  },

  getItemInfoFromDOM: function() {
    if ($('[form=js-carouselForm]').length > 0) {
      var carouselInfoObj = {
        itemId: $('#js-objectViewport').data('item_id') || $('[form=js-carouselForm][name=itemId]').val() || '',
        referral: $('[form=js-carouselForm][name=referral]').val() || '',
        referralName: $('[form=js-carouselForm][name=referralName]').val() || '',
      };

      carouselInfoObj.itemNumber =
        $('.js-item-link[data-item_id="' + carouselInfoObj.itemId + '"]').data('item_number') ||
        $('[form=js-carouselForm][name=itemNumber]').val() ||
        '';

      if (carouselInfoObj.referral === 'collection') {
        carouselInfoObj.collection_data = parseInt($('[form=js-carouselForm][name=collection_url]').val());
      }
      if (carouselInfoObj.referral === 'institution') {
        carouselInfoObj.repository_data = parseInt($('[form=js-carouselForm][name=repository_url]').val());
      }
      if (carouselInfoObj.referral === 'campus') {
        carouselInfoObj.campus_slug = $('[form=js-carouselForm][name=campus_slug]').val();
      }

      return carouselInfoObj;
    } else {
      console.log('[ERROR]: QueryManager attempting to retrieve item information from js-carouselForm when no such form is in DOM.');
      return {};
    }
  },

  unsetItemInfo: function() {
    this.unset('itemId', {silent: true});
    this.unset('itemNumber', {silent: true});

    if (this.get('referral') !== undefined) {
      if (this.get('referral') === 'institution') {
        this.unset('repository_data', {silent: true});
      } else if (this.get('referral') === 'campus') {
        this.unset('campus_slug', {silent: true});
      } else if (this.get('referral') === 'collection') {
        this.unset('collection_data', {silent: true});
      }
      this.unset('referral', {silent: true});
      this.unset('referralName', {silent: true});
    }
  },

  initialize: function() {
    var attributes;
    if ($('[form=js-facet]').length) {
      attributes = this.getQueryFromDOM('js-facet');
    }
    else if ($('[form=js-carouselForm]').length) {
      attributes = this.getQueryFromDOM('js-carouselForm');
      attributes = _.extend(attributes, this.getItemInfoFromDOM());
    }

    attributes = _.omit(attributes, function(value) {
      return _.isNull(value);
    });
    this.set(attributes);
  },

  set: function(key, value, options) {
    if (key === null) { return this; }
    
    var attrs;
    if (typeof key === 'object') {
      attrs = key;
      options = value;
    } else {
      (attrs = {})[key] = value;
    }
    
    options = options || {};
        
    // if we're setting an attribute to default, remove it from the list
    _.each(attrs, (function(that) {
      return function(value, key, list) {
        if (value !== undefined) {
          if ((that.defaultValues[key] !== undefined && that.defaultValues[key] === value) || (value.length === 0 && key !== 'q')) {
            delete list[key];
            // that.unsetSessionStorage(key);
            if (_.isEmpty(list)) {
              that.unset(key);
            } else {
              that.unset(key, {silent: true});
            }
          }          
        }
      };
    }(this)));
        
    Backbone.Model.prototype.set.apply(this, [attrs, options]);
  }
});
