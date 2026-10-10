from django.db import transaction
from rest_framework import serializers
from base_feature_app.models import Sale, SoldProduct, Product
from base_feature_app.serializers.product import ProductSerializer

class SoldProductSerializer(serializers.ModelSerializer):
    product_id = serializers.IntegerField(write_only=True)
    product = ProductSerializer(read_only=True)

    def validate_product_id(self, value):
        if not Product.objects.filter(pk=value).exists():
            raise serializers.ValidationError('Product is not available.')
        return value

    class Meta:
        model = SoldProduct
        fields = ['product_id', 'product', 'quantity']

class SaleSerializer(serializers.ModelSerializer):
    sold_products = SoldProductSerializer(many=True)

    class Meta:
        model = Sale
        fields = '__all__'

    @transaction.atomic
    def create(self, validated_data):
        sold_products_data = validated_data.pop('sold_products')
        product_ids = {item['product_id'] for item in sold_products_data}
        # Keep referenced products available until every line is persisted.
        products = {
            product.pk: product
            for product in Product.objects.select_for_update()
            .filter(pk__in=product_ids).order_by('pk')
        }
        if product_ids - products.keys():
            raise serializers.ValidationError({
                'sold_products': ['Product is no longer available.'],
            })

        sale = Sale.objects.create(**validated_data)
        for sold_product_data in sold_products_data:
            product_id = sold_product_data.pop('product_id')
            sold_product = SoldProduct.objects.create(
                product=products[product_id], **sold_product_data,
            )
            sale.sold_products.add(sold_product)
        return sale
