import logging
import os
from functools import partial

from django.core.files.storage import storages
from django.db import models, transaction
from django.db.models.signals import post_delete, pre_save
from easy_thumbnails.conf import settings
from easy_thumbnails.files import get_thumbnailer
from easy_thumbnails.models import Thumbnail
from easy_thumbnails.utils import get_storage_hash

logger = logging.getLogger('django.db.models')

def delete_files(sender, instance, *args, **kwargs): #pylint: disable=unused-argument
    alias = kwargs['using']
    for field in instance._meta.fields:
        if not isinstance(field, models.FileField):
            continue
        file_to_delete = getattr(instance, field.name)
        if not file_to_delete.name:
            continue
        name = str(file_to_delete.name)
        storage = file_to_delete.storage
        thumbnail_storage = storages[settings.THUMBNAIL_DEFAULT_STORAGE]
        thumbnail_hash = get_storage_hash(thumbnail_storage)
        thumbnails = tuple(Thumbnail.objects.using(alias).filter(
            source__storage_hash=get_storage_hash(storage), source__name=name,
            storage_hash=thumbnail_hash,
        ).values_list('pk', 'name'))
        transaction.on_commit(partial(
            _delete_committed_files, name, storage, thumbnail_storage,
            thumbnail_hash, thumbnails, alias,
        ), using=alias)


def _delete_committed_files(name, storage, thumbnail_storage, thumbnail_hash, thumbnails, alias):
    """Clean captured files only after the emitting database commits."""
    for thumbnail_id, thumbnail_name in thumbnails:
        thumbnail_storage.delete(thumbnail_name)
        Thumbnail.objects.using(alias).filter(
            pk=thumbnail_id, name=thumbnail_name, storage_hash=thumbnail_hash,
        ).delete()
    if storage.exists(name):
        try:
            file_path = storage.path(name)
            storage.delete(name)
            remove_empty_directories(os.path.dirname(file_path))
        except IOError:
            # SQL is already committed; failure leaves pending file cleanup.
            logger.error('File not deleted: %s', name)

def delete_old_files(sender, instance, *args, **kwargs): #pylint: disable=unused-argument
    if not instance.pk:
        return

    try:
        old_instance = instance.__class__.objects.get(pk=instance.pk)
    except instance.__class__.DoesNotExist:
        return

    for field in instance._meta.fields:
        if not isinstance(field, models.FileField):
            continue
        old_file = getattr(old_instance, field.name)
        new_file = getattr(instance, field.name)
        if new_file != old_file:
            delete_file(old_file)

def delete_file(file_instance):
    if not file_instance.name:
        return
    thumbnailer = get_thumbnailer(file_instance)
    thumbnailer.thumbnail_storage = storages[settings.THUMBNAIL_DEFAULT_STORAGE]
    thumbnailer.delete_thumbnails()
    storage = file_instance.storage
    file_path = file_instance.path
    
    if storage and storage.exists(file_instance.name):
        try:
            storage.delete(file_instance.name)
            # Check if the directory is empty and remove it if it is
            remove_empty_directories(os.path.dirname(file_path))
        except IOError:
            logger.error('File not deleted: %s', file_instance.name)

def remove_empty_directories(path):
    """Recursively remove empty directories."""
    if not os.listdir(path):  # Check if the directory is empty
        os.rmdir(path)  # Remove the directory
        parent_directory = os.path.dirname(path)
        if parent_directory != path:  # Ensure we don't go beyond the root directory
            remove_empty_directories(parent_directory)

def register_cleaner_for_model(model_cls):
    post_delete.connect(delete_files, sender=model_cls)
    pre_save.connect(delete_old_files, sender=model_cls)
