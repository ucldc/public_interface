from .es_cache_retry import search_es, es_get, es_mlt
from .cache_retry import search_solr, SOLR_get, SOLR_mlt


class ItemManager(object):
    def __init__(self, index):
        self.index = index

    def search(self, query):
        if self.index == "solr":
            results = search_solr(query)
        elif self.index == "es":
            results = search_es(query)
        return results

    def get(self, item_id):
        if self.index == "es":
            item_search = es_get(item_id)
        elif self.index == "solr":
            item_id_search_term = 'id:"{0}"'.format(item_id)
            item_search = SOLR_get(q=item_id_search_term)
        return item_search

    def more_like_this(self, item_id):
        if self.index == "es":
            results = es_mlt(item_id)
        elif self.index == "solr":
            results = SOLR_mlt(item_id)
        return results

