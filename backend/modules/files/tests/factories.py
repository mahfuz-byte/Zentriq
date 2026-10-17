"""Test data for files (BUILD_PLAN §9.3). Create rows inside `tenant_context(...)`."""

import factory

from modules.files.models import FileObject


class FileObjectFactory(factory.django.DjangoModelFactory[FileObject]):
    class Meta:
        model = FileObject

    storage_key = factory.Sequence(lambda n: f"files/{n:08d}")
    mime_type = "image/png"
    size_bytes = 2048
    sha256 = "a" * 64
    purpose = FileObject.Purpose.SCHOOL_LOGO
