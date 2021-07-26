
class SearchForm(object):
    def __init__(self, params):
        
        self.context = {
            'q': params.get('q', ''),
            'rq': params.getlist('rq'),
            'rows': params.get('rows', '24'),
            'start': params.get('start', 0),
            'sort': params.get('sort', 'relevance'),
            'view_format': params.get('view_format', 'thumbnails'),
            'rc_page': params.get('rc_page', 0)
        }
