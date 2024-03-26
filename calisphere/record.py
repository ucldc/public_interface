from copy import deepcopy
from urllib.parse import quote
from .es_cache_retry import json_loads_url
from typing import Any, Dict
from django.conf import settings
from django.http import Http404
from .collection_views import Collection
from .institution_views import Repository

def get_iiif(media_id, index) -> Dict[str, Any]:
    if index == 'solr':
        iiif_url = f"{settings.UCLDC_IIIF_SOLR}{media_id}/info.json"
    else:
        iiif_url = f"{settings.UCLDC_IIIF}{quote(media_id)}/info.json"

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
        content_file.update(get_iiif(structmap['id'], 'solr'))
    if format == 'file':
        content_file.update({
            'id': structmap['id'],
            'url': f"{settings.UCLDC_NUXEO_THUMBS_SOLR}{structmap['id']}"
        })
    if format == 'audio':
        content_file.update({
            'id': structmap['id'],
            'url': f"{settings.UCLDC_MEDIA_SOLR}{structmap['id']}"
        })
    if format == 'video':
        content_file.update({
            'id': structmap['id'],
            'url': f"{settings.UCLDC_MEDIA_SOLR}/{structmap['id']}",
            'poster': f"{settings.UCLDC_NUXEO_THUMBS_SOLR}{structmap['id']}"
        })

    return content_file


def get_hosted_content_file(media, thumbnail_md5):
    format = media.get('format','')
    content_file = {'format': format}

    if format =='image':
        content_file.update(get_iiif(media['media_key'], 'es'))
    if format == 'file':
        content_file.update({
            'id': f"media/{media['media_key']}",
            'url': f"{settings.UCLDC_NUXEO_THUMBS}thumbnails/{thumbnail_md5}"
        })
    if format == 'audio':
        content_file.update({
            'id': f"media/{media['media_key']}",
            'url': f"{settings.UCLDC_MEDIA}media/{media['media_key']}"
        })
    if format == 'video':
        content_file.update({
            'id': f"media/{media['media_key']}",
            'url': f"{settings.UCLDC_MEDIA}media/{media['media_key']}",
            'poster': f"{settings.UCLDC_NUXEO_THUMBS}thumbnails/{thumbnail_md5}"
        })

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
                complex_object_display['selectedComponent'] = self.get_child_metadata(
                    int(child_index))

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

    def has_media(self, child=None):
        if self.index == 'solr':
            if child:
                return 'format' in child
            else:
                return 'format' in self.get_media_json()
        elif self.index == 'es':
            if child:
                return 'media' in child
            else:
                return 'media' in self.indexed_record

    def get_media(self, child_index=None):
        content_file = None

        if child_index and self.is_complex():
            child = self.get_child(int(child_index))
            if self.has_media(child) and self.index == 'solr':
                content_file = get_solr_hosted_content_file(child)

        elif self.has_media():
            if self.index == 'solr':
                content_file = get_solr_hosted_content_file(self.get_media_json())
            else:
                content_file = get_hosted_content_file(
                    self.indexed_record.get('media'), 
                    self.indexed_record.get('reference_image_md5')
                )

        elif self.is_complex():
            if self.index == 'solr':
                content_file = get_solr_hosted_content_file(self.get_child(0))

        return content_file

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

    def get_child(self, index) -> Dict[str, Any]:
        try:
            return self.get_children()[index]
        except IndexError:
            raise Http404(f"Child {index} not found")

    def get_relations(self):
        if self.index == 'solr':
            return self.indexed_record.get('relation', [])
        return []

    def get_child_metadata(self, child_index):
        child = self.get_child(child_index)

        child_display: Dict[str, Any] = {'selected': True}
        # remove emptry strings from child values
        for field, values in child.items():
            if isinstance(values, list) and isinstance(values[0], str):
                child_display[field] = [
                    val for val in values if val and val.strip()
                ]
        child_display = dict((k, v) for k, v in list(child_display.items()) if v)

        return child_display