from copy import deepcopy
import dataclasses
from urllib.parse import quote
from .utils import json_loads_url
from typing import Any, Dict, Union, List
from django.conf import settings
from django.http import Http404
from .collection_views import Collection
from .institution_views import Repository

def get_iiif(iiif_url) -> Dict[str, Any]:
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
        iiif_url = f"{settings.SOLR_IIIF}{structmap['id']}/info.json"
        content_file.update(get_iiif(iiif_url))
    if format == 'file':
        content_file.update({
            'id': structmap['id'],
            'url': f"{settings.SOLR_MEDIA}{structmap['id']}",
            'poster': f"{settings.SOLR_NUXEO_THUMBS}{structmap['id']}"
        })
    if format == 'audio':
        content_file.update({
            'id': structmap['id'],
            'url': f"{settings.SOLR_MEDIA}{structmap['id']}"
        })
    if format == 'video':
        content_file.update({
            'id': structmap['id'],
            'url': f"{settings.SOLR_MEDIA}{structmap['id']}",
            'poster': f"{settings.SOLR_NUXEO_THUMBS}{structmap['id']}"
        })

    return content_file


def get_hosted_content_file(media, thumbnail_md5):
    format = media.get('format','')
    content_file = {'format': format}

    if format =='image':
        iiif_url = f"{settings.UCLDC_IIIF}{quote(media['media_key'])}/info.json"
        content_file.update(get_iiif(iiif_url))
    if format == 'file':
        content_file.update({
            'id': f"media/{quote(media['media_key'])}",
            'url': f"{settings.UCLDC_MEDIA}media/{quote(media['media_key'])}",
            'poster': f"{settings.UCLDC_NUXEO_THUMBS}thumbnails/{thumbnail_md5}"
        })
    if format == 'audio':
        content_file.update({
            'id': f"media/{quote(media['media_key'])}",
            'url': f"{settings.UCLDC_MEDIA}media/{quote(media['media_key'])}"
        })
    if format == 'video':
        content_file.update({
            'id': f"media/{quote(media['media_key'])}",
            'url': f"{settings.UCLDC_MEDIA}media/{quote(media['media_key'])}",
            'poster': f"{settings.UCLDC_NUXEO_THUMBS}thumbnails/{thumbnail_md5}"
        })

    return content_file


def make_solr_carousel_display(child):
    format = child.get('format', '').lower()
    child_id = child['id']
    if format == 'image':
        child['carousel_thumbnail'] = (
            f"{ settings.SOLR_IIIF }{ child_id }"
            "/full/,80/0/default.jpg"
        )
    if format == 'file':
        child['carousel_thumbnail'] = (
            f"{ settings.SOLR_NUXEO_THUMBS }{ child_id }"
        )
    if format == 'video': 
        child['carousel_thumbnail'] = (
            f"{ settings.SOLR_NUXEO_THUMBS }{ child_id }"
        )
    return child


def make_es_carousel_display(child):
    # label and format are both used by the carousel - they were part
    # of the media_json schema in the Solr index
    media_json_schema = {
        'label': child.get('title', [''])[0],
        'format': child.get('media', {}).get('format', '')
    }
    child.update(media_json_schema)

    format = child.get('media', {}).get('format', '')
    if format == 'image':
        child['carousel_thumbnail'] = (
            f"{ settings.UCLDC_IIIF }{ quote(child['media']['media_key']) }"
            "/full/,80/0/default.jpg"
        )
    if format == 'file':
        child['carousel_thumbnail'] = (
            f"{ settings.UCLDC_NUXEO_THUMBS }{ child['thumbnail_key'] }"
        )
    if format == 'video':
        child['carousel_thumbnail'] = (
            f"{ settings.UCLDC_NUXEO_THUMBS }{ child['thumbnail_key'] }"
        )
    return child


def remove_empty_values(child):
    # remove emptry strings from child values
    child_display: Dict[str, Any] = {}
    for field, values in child.items():
        if isinstance(values, list) and isinstance(values[0], str):
            child_display[field] = [
                val for val in values if val and val.strip()
            ]
    child_display = dict((k, v) for k, v in list(child_display.items()) if v)

    return child_display


@dataclasses.dataclass
class MediaJsonSchema:
    label: str
    alternativeTitle: Union[list, str]
    creator: Union[list, str]
    contributor: Union[list, str]
    publisher: Union[list, str]
    rights: Union[list, str]
    rightsHolder: Union[list, str]
    rightsNote: Union[list, str]
    dateCopyrighted: Union[list, str]
    description: Union[list, str]
    type: Union[list, str]
    format: Union[list, str]
    genre: Union[list, str]
    extent: Union[list, str]
    identifier: Union[list, str]
    subject: Union[list, str]
    temporalCoverage: Union[list, str]
    spatial: Union[list, str]
    source: Union[list, str]
    relation: Union[list, str]
    provenance: Union[list, str]
    location: Union[list, str]
    transcription: Union[list, str]
    date: Union[list, str] 
    # date can be a list of dictionaries with a key "displayDate"
    # in this case, we only care about the first dictionary's display date
    language: List[Dict[str,str]]
    # language must be a list of dictionaries with a key "iso639_3"
    # we only care about the first one dictionary's iso639_3


def analyze_media_json_vs_es_child_fields(child):
    # Temporary Analysis of MediaJsonSchema fields vs. child.keys()
    # TODO: Remove this once analysis is complete
    # get MediaJsonSchema field names and compare to child.keys() 
    # print fields in MediaJsonSchema that are not in child.keys()
    # print fields in child.keys() that are not in MediaJsonSchema
    # and are candidates to map to missing MediaJsonSchema fields

    # Collect Field Name Data
    media_json_field_names = [
        f.name for f in dataclasses.fields(MediaJsonSchema)]
    es_field_names = child.keys()

    # these won't be in media_json
    known_rikolti_additions = {
        'collection_name', 'collection_url', 'collection_data', 
        'sort_collection_data',
        'repository_name', 'repository_url', 'repository_data', 
        'campus_name', 'campus_url', 'campus_data',
        'thumbnail', 'media', 'thumbnail_key', 'carousel_thumbnail',
        'mapper_type', 'fetcher_type', 
        'sort_title', 'url_item', 'calisphere-id', 'id'
    }
    # these are known mappings
    known_mappings = {
        'title': 'label', 
        'rights_holder': 'rightsHolder', 
        'alternative_title': 'alternativeTitle'
    }

    # Start analysis
    missing_media_json_fields = list(
        set(media_json_field_names) - set(es_field_names)
        - set(known_mappings.values())
    )
    extra_es_fields = list(
        set(es_field_names) - set(media_json_field_names)
        - known_rikolti_additions - set(known_mappings.keys())
    )
    print(
        f"{'>'*72}\n"
        "Missing media_json fields for this record:\n"
        f"{missing_media_json_fields}"
        f"\n{'-'*72}\n"
        "Extra rikolti fields for this record:\n"
        "(could these be mapped to any missing fields listed above?)\n"
        f"{extra_es_fields}"
        f"\n{'<'*72}\n"
    )


def map_es_child_to_media_json_schema(child):
    # Map Rikolti Child to the Media Json Schema
    # TODO: transition to using child schema in the future

    analyze_media_json_vs_es_child_fields(child)

    child['label']  = child.get('title', [''])[0]
    child['format'] = child.get('media', {}).get('format', '')
    if child.get('rights_holder'):
        child['rightsHolder'] = child['rights_holder']
    if child.get('alternative_title'):
        child['alternativeTitle'] = child['alternative_title']

    return child


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
                selectedComponent = self.get_child(int(child_index))
                if self.index == 'es':
                    selectedComponent = map_es_child_to_media_json_schema(
                        selectedComponent)
                selectedComponent.update({'selected': True})
                complex_object_display['selectedComponent'] = selectedComponent

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
            return bool('nuxeo.nuxeo' in self.indexed_record.get('mapper_type'))

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
            elif self.has_media(child):
                content_file = get_hosted_content_file(
                    child['media'], child.get('thumbnail_key')
                )

        elif self.has_media():
            if self.index == 'solr':
                content_file = get_solr_hosted_content_file(self.get_media_json())
            else:
                content_file = get_hosted_content_file(
                    self.indexed_record.get('media'), 
                    self.indexed_record.get('reference_image_md5')
                )

        elif self.is_complex():
            first_child = self.get_child(0)
            if self.has_media(first_child) and self.index == 'solr':
                content_file = get_solr_hosted_content_file(self.get_child(0))
            elif self.has_media(first_child):
                content_file = get_hosted_content_file(
                    self.get_child(0)['media'], 
                    self.get_child(0).get('thumbnail_key')
                )

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
                self.children = [
                    make_solr_carousel_display(child) for child in
                    self.get_media_json().get('structMap', [])
                ]
            else:
                self.children = [
                    make_es_carousel_display(child) for child in 
                    self.indexed_record.get('children', [])
                ]
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
