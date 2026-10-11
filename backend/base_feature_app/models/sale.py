from django.db import models, router, transaction
from base_feature_app.models import Product

class SoldProduct(models.Model):
    """
    Model representing a product in the cart.
    """
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.product.title} (Qty: {self.quantity})'

class Sale(models.Model):
    """
    Model representing a sale.
    """
    email = models.EmailField()
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    sold_products = models.ManyToManyField(SoldProduct)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.email

    def delete(self, using=None, keep_parents=False):
        alias = using or router.db_for_write(type(self), instance=self)
        with transaction.atomic(using=alias):
            line_ids = list(self.sold_products.using(alias).values_list('pk', flat=True))
            super().delete(using=alias, keep_parents=keep_parents)
            # A line can still belong to another sale through the M2M relation.
            SoldProduct.objects.using(alias).filter(
                pk__in=line_ids, sale__isnull=True,
            ).delete()
