from copy import deepcopy
from .es_cache_retry import json_loads_url
from typing import Any, Dict
from django.conf import settings
from django.http import Http404
from .collection_views import Collection
from .institution_views import Repository

def get_iiif(media_id) -> Dict[str, Any]:
    iiif_url = f"{settings.UCLDC_IIIF}{media_id}/info.json"
    if iiif_url.startswith('//'):
        iiif_url = ''.join(['http:', iiif_url])

    iiif_info = json_loads_url(iiif_url)
    if not iiif_info:
        return {}
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

    return {
        'titleSources': iiif_info,
        'size': access_size,
        'url': access_url
    }


def get_solr_hosted_content_file(structmap):
    format = structmap['format']
    content_file = {'format': format}

    if format == 'image':
        content_file.update(get_iiif(structmap['id']))
    if format == 'file':
        content_file.update({'id': structmap['id']})
    if format in ['audio', 'video']:
        content_file.update({
            'id': structmap['id'],
            'url': f"{settings.UCLDC_MEDIA}/{structmap['id']}"
        })

    return content_file


def get_hosted_content_file(media, thumbnail_md5):
    format = media.get('format','')
    content_file = {'format': format}

    if format =='image':
        content_file.update(get_iiif(media['media_key']))
    if format == 'file':
        content_file.update({'id': f"thumbnails/{thumbnail_md5}"})
    if format in ['audio', 'video']:
        content_file.update({
            'id': f"thumbnails/{thumbnail_md5}",
            'url': f"{settings.UCLDC_NUXEO_THUMBS}media/{media['media_key']}"
        })
    return content_file


def hosted_object(item, child_index=None, index='es'):
    content_file = None

    if (item.has_media() and not child_index):
        if index == 'solr':
            content_file = get_solr_hosted_content_file(item.get_media_json())
        else:
            content_file = get_hosted_content_file(
                item.indexed_record.get('media'), 
                item.indexed_record.get('reference_image_md5')
            )

    elif item.is_complex() and child_index:
        if index == 'solr':
            try:
                component = item.get_children()[int(child_index)]
            except IndexError:
                raise Http404(f"Component {child_index} not found")
            if 'format' in component:
                content_file = get_solr_hosted_content_file(component)

    elif item.is_complex():
        if index == 'solr':
            media_data = item.get_children()[0]
            content_file = get_solr_hosted_content_file(media_data)

    return content_file


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
                complex_object_display['selectedComponent'] = self.get_component(int(child_index))

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

    def get_component(self, child_index):
        try:
            child = self.get_children()[child_index]
        except IndexError:
            raise Http404(f"Component {child_index} not found")

        component_display: Dict[str, Any] = {'selected': True}
        # remove emptry strings from child values
        for field, values in child.items():
            if isinstance(values, list) and isinstance(values[0], str):
                component_display[field] = [
                    val for val in values if val and val.strip()
                ]
        component_display = dict((k, v) for k, v in list(component_display.items()) if v)

        return component_display