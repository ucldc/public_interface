from .cache_retry import search_solr, SOLR_get, SOLR_mlt
try:
    from .es_cache_retry import search_es, es_get, es_mlt
    ES = True
except ImportError:
    ES = False


class ItemManager(object):
    def __init__(self, index='solr'):
        if ES is True:
            self.index = index
        else:
            self.index = 'solr'

    def search(self, query):
        if self.index == "solr":
            results = search_solr(query)
        elif self.index == "es":
            results = search_es(query)
        return results

    def get(self, item_id):
        if self.index == 'es':
            item_search = es_get(item_id)
        else:
            item_id_search_term = 'id:"{0}"'.format(item_id)
            item_search = SOLR_get(q=item_id_search_term)
        return item_search

    def more_like_this(self, item_id):
        if self.index == 'es':
            results = es_mlt(item_id)
        else:
            results = SOLR_mlt(item_id)
        return results


