from django.core.files import uploadhandler
from md5s3stash import md5s3stash
from public_interface import settings
from collections import namedtuple


class Md5s3stashUploadHandler(uploadhandler.FileUploadHandler):
    def receive_data_chunk(self, raw_data, start):
        return raw_data

    def file_complete(self, file_size):
        url = "file:///" + settings.MEDIA_ROOT + "/uploads/" + self.file_name
        report = md5s3stash(url, "static-ucldc-cdlib-org/harvested_images")
        S3UploadedFile = namedtuple('S3UploadedFile',
                                    'name, size, content_type')
        return S3UploadedFile(report.md5, file_size, self.content_type)
