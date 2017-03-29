/*global Backbone */
/*global _ */
/*exported QueryManager */

'use strict';

var QueryManager = Backbone.Model.extend({
  
  defaultValues: {
    // q: '',
    rq: '',
    view_format: 'thumbnails',
    sort: 'relevance', 
    rows: '24',
    start: 0
  },
  
  getQueryFromDOM: function() {
    if ($('#js-facet').length > 0) {
      var queryObj = {
        q: $('[form=js-facet][name=q]').val(),
        view_format: $('[form=js-facet][name=view_format]').val(),
        sort: $('[form=js-facet][name=sort]').val(),
        rows: $('[form=js-facet][name=rows]').val(),
        start: parseInt($('[form=js-facet][name=start]').val()),
      };
      var filters = $('[form=js-facet].js-facet').serializeArray();
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
      var refineArray = $('[form=js-facet][name=rq]').serializeArray();
      if (refineArray > 0) {
        queryObj.rq = [];
        for (var j=0; j<refineArray.length; j++) {
          if (refineArray[j].value !== '') {
            queryObj.rq.push(refineArray[j].value);
          }
        }
      }
      return queryObj;
    } else {
      console.log('[ERROR]: QueryManager attempting to retrieve query parameters from facet form when no facet form is in DOM.');
      return {};
    }
  },

  initialize: function() {
    var attributes;
    if (sessionStorage.length > 0) {
      attributes = {
        q: sessionStorage.getItem('q'),
        rq: JSON.parse(sessionStorage.getItem('rq')),
        view_format: sessionStorage.getItem('view_format'),
        sort: sessionStorage.getItem('sort'),
        start: sessionStorage.getItem('start'),
        type_ss: JSON.parse(sessionStorage.getItem('type_ss')),
        facet_decade: JSON.parse(sessionStorage.getItem('facet_decade')),
        repository_data: JSON.parse(sessionStorage.getItem('repository_data')),
        collection_data: JSON.parse(sessionStorage.getItem('collection_data')),
        campus_slug: sessionStorage.getItem('campus_slug'),
        itemNumber: sessionStorage.getItem('itemNumber'),
        itemId: sessionStorage.getItem('itemId'),
        referral: sessionStorage.getItem('referral'),
        referralName: sessionStorage.getItem('referralName')
      };
      attributes = _.omit(attributes, function(value) {
        return _.isNull(value);
      });
      this.set(attributes);
    } 
    else if ($('#js-facet').length > 0) {
      attributes = this.getQueryFromDOM();
      this.set(attributes);
    }
  },
  
  setSessionStorage: function(value, key) {
    if (_.isArray(value)) {
      sessionStorage.setItem(key, JSON.stringify(value));
    } else {
      sessionStorage.setItem(key, value);
    }
  },
  
  unsetSessionStorage: function(value, key) {
    if (key === undefined) {
      key = value;
    }
    sessionStorage.removeItem(key);
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
            that.unsetSessionStorage(key);
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
    
    if (!options.unset) {
      _.each(attrs, this.setSessionStorage);
    } else {
      _.each(attrs, this.unsetSessionStorage);
    }
  },
    
  clear: function() {
    Backbone.Model.prototype.clear.apply(this, arguments);
    sessionStorage.clear();
  }, 
});
