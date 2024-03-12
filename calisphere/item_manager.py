from .es_cache_retry import search_es, es_get, es_mlt

class ItemManager(object):

    def search(self, query):
        return search_es(query)

    def get(self, item_id):
        return es_get(item_id)

    def more_like_this(self, item_id):
        return es_mlt(item_id)
