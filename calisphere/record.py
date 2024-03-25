from copy import deepcopy
from .es_cache_retry import json_loads_url
from django.conf import settings
from .collection_views import Collection
from .institution_views import Repository


def get_solr_hosted_content_file(structmap):
    content_file = ''
    if structmap['format'] == 'image':
        iiif_url = '{}{}/info.json'.format(settings.UCLDC_IIIF,
                                           structmap['id'])
        if iiif_url.startswith('//'):
            iiif_url = ''.join(['http:', iiif_url])
        iiif_info = json_loads_url(iiif_url)
        if not iiif_info:
            return None
        size = iiif_info.get('sizes', [])[-1]
        if size['height'] > size['width']:
            access_size = {
                'width': ((size['width'] * 1024) // size['height']),
                'height': 1024
            }
            access_url = iiif_info['@id'] + "/full/,1024/0/default.jpg"
        else:
            access_size = {
                'width': 1024,
                'height': ((size['height'] * 1024) // size['width'])
            }
            access_url = iiif_info['@id'] + "/full/1024,/0/default.jpg"

        content_file = {
            'titleSources': iiif_info,
            'format': 'image',
            'size': access_size,
            'url': access_url
        }
    if structmap['format'] == 'file':
        content_file = {
            'id': structmap['id'],
            'format': 'file',
        }
    if structmap['format'] == 'video':
        access_url = os.path.join(settings.UCLDC_MEDIA, structmap['id'])
        content_file = {
            'id': structmap['id'],
            'format': 'video',
            'url': access_url
        }
    if structmap['format'] == 'audio':
        access_url = os.path.join(settings.UCLDC_MEDIA, structmap['id'])
        content_file = {
            'id': structmap['id'],
            'format': 'audio',
            'url': access_url
        }

    return content_file


def get_hosted_content_file(item):
    content_file = ''
    media_data = item.get('media')
    media_path = media_data.get('path','')
    if media_path.startswith('s3://rikolti-content/jp2'):
        iiif_url = f"{settings.UCLDC_IIIF}{media_data['media_key']}/info.json"
        if iiif_url.startswith('//'):
            iiif_url = ''.join(['http:', iiif_url])
        iiif_info = json_loads_url(iiif_url)
        if not iiif_info:
            return None
        size = iiif_info.get('sizes', [])[-1]
        if size['height'] > size['width']:
            access_size = {
                'width': ((size['width'] * 1024) // size['height']),
                'height': 1024
            }
            access_url = iiif_info['@id'] + "/full/,1024/0/default.jpg"
        else:
            access_size = {
                'width': 1024,
                'height': ((size['height'] * 1024) // size['width'])
            }
            access_url = iiif_info['@id'] + "/full/1024,/0/default.jpg"

        content_file = {
            'titleSources': iiif_info,
            'format': 'image',
            'size': access_size,
            'url': access_url
        }
    if media_path.startswith('s3://rikolti-content/media'):
        if media_path.endswith('pdf'):
            thumbnail = item.get('thumbnail')
            content_file = {
                'id': f"thumbnails/{item.get('reference_image_md5')}",
                'format': 'file',
            }
        if media_path.endswith('mp3'):
            access_url = f"{settings.UCLDC_NUXEO_THUMBS}media/{media_data['media_key']}"
            content_file = {
                'id': f"thumbnails/{item.get('reference_image_md5')}",
                'format': 'audio',
                'url': access_url
            }
        if media_path.endswith('mp4'):
            access_url = f"{settings.UCLDC_NUXEO_THUMBS}media/{media_data['media_key']}"
            content_file = {
                'id': f"thumbnails/{item.get('reference_image_md5')}",
                'format': 'video',
                'url': access_url
            }

    return content_file


def get_component(media_json, order):
    component = media_json['structMap'][order]
    component['selected'] = True
    if 'format' in component:
        media_data = component

    # remove emptry strings from list
    for k, v in list(component.items()):
        if isinstance(v, list) and isinstance(v[0], str):
            component[k] = [
                name for name in v if name and name.strip()
            ]
    component = dict((k, v) for k, v in list(component.items()) if v)

    return component, media_data


def hosted_object(item, child_index=None, index='es'):
    component = None
    content_file = None

    if (item.has_media() and not child_index):
        if index == 'solr':
            content_file = get_solr_hosted_content_file(item.get_media_json())
        else:
            content_file = get_hosted_content_file(item.doc)

    elif item.is_complex() and child_index:
        if index == 'solr':
            component, media_data = get_component(item.get_media_json(), int(child_index))
            component = component
            content_file = get_solr_hosted_content_file(media_data)

    elif item.is_complex():
        if index == 'solr':
            media_data = item.get_children()[0]
            content_file = get_solr_hosted_content_file(media_data)

    return content_file, component


class Record(object):
    def __init__(self, indexed_record, child_index=None, index='es'):
        self.index = index
        self.indexed_record = indexed_record
        self.display = deepcopy(indexed_record)

        if 'reference_image_dimensions' in self.indexed_record:
            split_ref = self.display['reference_image_dimensions'].split(':')
            self.display['reference_image_dimensions'] = split_ref

        self.display['harvest_type'] = 'hosted' if self.is_hosted() else 'harvested'

        if self.is_complex():
            formats = set([
                c['format'] for c in self.get_children() if 'format' in c])
            all_images = all(f == 'image' for f in formats)

            complex_object_display = {
                'selected': not bool(child_index),
                'structMap': self.get_children(),
                'componentCount': len(self.get_children()),
                'multiFormat': True if len(formats) > 1 else False,
                'hasComponentCaptions': False if all_images else True,
                'has_fixed_thumb': bool(
                    self.indexed_record.get('reference_image_md5')),
            }
            if child_index:
                complex_object_display['selectedComponentIndex'] = child_index

            self.display.update(complex_object_display)

        if self.is_harvested():
            oac_display = {'oac': False}

            url_item = self.indexed_record.get('url_item', '')
            if url_item.startswith('http://ark.cdlib.org/ark:'):
                oac_display = {
                    'oac': True,
                    'url_item': url_item.replace(
                        'http://ark.cdlib.org/ark:',
                        'http://oac.cdlib.org/ark:'
                    ) + '/?brand=oac4'
                }
            self.display.update(oac_display)

        self.collections = [
            Collection(col_id, index) 
            for col_id in self.indexed_record.get('collection_ids')
        ]
        self.repositories = [
            Repository(repo_id, index) 
            for repo_id in self.indexed_record.get('repository_ids')
        ]

    def is_hosted(self):
        if self.index == 'solr':
            return bool(self.indexed_record.get('structmap_url'))
        elif self.index == 'es':
            return bool(self.indexed_record.get('media'))

    def is_harvested(self):
        return not self.is_hosted()

    def is_simple(self):
        return not self.is_complex()

    def is_complex(self):
        if self.index == 'solr':
            return 'structMap' in self.get_media_json()
        elif self.index == 'es':
            return 'children' in self.indexed_record

    def has_media(self):
        if self.index == 'solr':
            return 'format' in self.get_media_json()

    def get_media_json(self):
        if self.index == 'es' or not self.is_hosted():
            return {}
        
        if not hasattr(self, 'media_json'):
            structmap_url = self.indexed_record['structmap_url'].replace(
                's3://static', 'https://s3.amazonaws.com/static')
            self.media_json = json_loads_url(structmap_url)

        return self.media_json

    def get_children(self):
        if not hasattr(self, 'children'):
            if self.index == 'solr':
                self.children = self.get_media_json().get('structMap', [])
            else:
                self.children = []
        return self.children

    def get_relations(self):
        if self.index == 'solr':
            return self.indexed_record.get('relation', [])
        return []

