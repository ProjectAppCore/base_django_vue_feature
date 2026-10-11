from django.db import models, router, transaction
from django_attachments.models import Library
from django_attachments.fields import GalleryField

class Product(models.Model):
    """
    Product model.

    :ivar category: category product.
    :vartype category: str
    :ivar sub_category: subcategory product.
    :vartype sub_category: str
    :ivar title: title product.
    :vartype title: str
    :ivar description: description product.
    :vartype description: str
    :ivar price: price of the product.
    :vartype price: int
    :ivar gallery: gallery of images associated with the product.
    :vartype gallery: Gallery
    :ivar categoria: category of the product in Spanish.
    """

    title = models.CharField(max_length=40)
    category = models.CharField(max_length=40)
    sub_category = models.CharField(max_length=40)    
    description = models.TextField()

    price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    gallery = GalleryField(related_name='products_with_attachment', on_delete=models.CASCADE)

    def __str__(self):
        return self.title

    def delete(self, using=None, keep_parents=False):
        alias = using or router.db_for_write(type(self), instance=self)
        with transaction.atomic(using=alias):
            library = None
            if self.gallery_id is not None:
                library = Library.objects.using(alias).select_for_update().filter(
                    pk=self.gallery_id,
                ).first()
            # PROTECT must succeed before touching the library or its files.
            super().delete(using=alias, keep_parents=keep_parents)
            if library is not None and not (
                library.products_with_attachment.using(alias).exists()
                or library.blog_image.using(alias).exists()
            ):
                library.delete(using=alias)
