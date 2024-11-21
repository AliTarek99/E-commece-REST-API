from ..models import Orders, OrdersItems
from cart.models import Cart
from django.db import transaction
from products.models import ProductVariant, ProductImages
from django.db.models import OuterRef, Subquery
from django.db.models.functions import Coalesce
from rest_framework import status


import json

class OrdersServices:
    @classmethod
    def create_order(self, user, address):
        
        try:
            cart = Cart.objects.filter(user=user).only(
                'user_id',  
                'quantity', 
                'product_variant'
            ).select_related(
                'product_variant', 
                'product_variant__color', 
                'product_variant__size', 
                'product_variant__parent'
            ).annotate(
                default_image=Coalesce(
                    Subquery(
                        ProductImages.objects.filter(
                            product_id=OuterRef('product_variant__parent_id'),
                            color=OuterRef('product_variant__color'),
                            default=True
                        ).values('url')[:1]
                    ),
                    Subquery(
                        ProductImages.objects.filter(
                            product_id=OuterRef('product_variant__parent_id'),
                            color=OuterRef('product_variant__color')
                        ).values('url')[:1]
                    )
                )
            ).all()
            
            if len(list(cart)) == 0:
                return None

            total_price = sum([item.product_variant.price * item.quantity for item in cart])
            
            with transaction.atomic():
                order = Orders.objects.create(user=user, total_price=total_price, address=address)

                order_items = {}
                variants = []
                for item in cart:
                    order_item = OrdersItems(
                        order=order,
                        product_variant_id=item.product_variant_id,
                        quantity=item.quantity,
                        price=item.product_variant.price,
                        size=item.product_variant.size,
                        description=item.product_variant.parent.description,
                        color=item.product_variant.color,
                        name=item.product_variant.parent.name,
                        seller_id=item.product_variant.parent.seller_id,
                        image_url=item.default_image
                    )
                    order_items[f'{order_item.product_variant_id}'] = order_item
                    variants.append(item.product_variant_id)
                
                products = ProductVariant.objects.filter(id__in=variants).select_for_update().all()
                for product in products:
                    product.quantity = product.quantity - order_items.get(f'{product.id}').quantity
                    if product.quantity < 0:
                        Cart.objects.filter(user_id=user.id, product_variant_id=product.id).update(
                            quantity=product.quantity + order_items.get(f'{product.id}').quantity
                        )
                        e = Exception("Not enough items in stock!")
                        e.status_code = 400
                        raise e
                ProductVariant.objects.bulk_update(products, ['quantity'], batch_size=500)

                OrdersItems.objects.bulk_create(order_items.values())
                Cart.objects.filter(user_id=user.id).delete()
                return order
        except Exception as e:
            if hasattr(e, 'status_code'):
                raise e
            else:
                print(e)
                raise Exception("Something went wrong!")
        
    @classmethod
    def restore_items(cls, order, user):
        with transaction.atomic():
            cls.return_items_to_cart(user=user, order=order)
            cls.return_items_to_stock(order)
            order.delete()
        
    @classmethod
    def reorder(cls, user, order_id):
        try:
            order = Orders.objects.filter(id=order_id, user=user).first()
            if not order:
                error = Exception('Order not found')
                error.status = status.HTTP_404_NOT_FOUND
                raise error
            
            with transaction.atomic():
                Cart.objects.filter(user=user).delete()
                cls.return_items_to_cart(order, user)
                
        except Exception as e:
            if hasattr(e, 'status'):
                raise e
            else:
                error = Exception('Something went wrong')
                error.status = status.HTTP_500_INTERNAL_SERVER_ERROR
                print("Error while adding product to cart:", e)
                raise error
            
    @classmethod
    def return_order(cls, user, order_id):
        try:
            with transaction.atomic():
                order = Orders.objects.filter(id=order_id, user=user).select_for_update().first()
                if not order:
                    error = Exception('Order not found')
                    error.status = status.HTTP_404_NOT_FOUND
                    raise error
                if order.status != Orders.DELIVERED:
                    error = Exception('Order is not delivered yet')
                    error.status = status.HTTP_400_BAD_REQUEST
                    raise error
                order.status = Orders.RETURNED
                order.save(update_fields=['status'])
                
                cls.return_items_to_stock(order)
        except Exception as e:
            if hasattr(e, 'status'):
                raise e
            else:
                error = Exception('Something went wrong')
                error.status = status.HTTP_500_INTERNAL_SERVER_ERROR
                print("Error while returning order:", e)
                raise error
          
    @classmethod
    def return_items_to_stock(self, order):
        order_items = OrdersItems.objects.filter(order=order).select_related('product_variant').all()
        variants_to_update = []
        for item in order_items:
            if item.product_variant is None:
                continue
            item.product_variant.quantity = item.product_variant.quantity + item.quantity
            item.product_variant.save(update_fields=['quantity'])
            variants_to_update.append(item.product_variant)
        ProductVariant.objects.bulk_update(variants_to_update, ['quantity'], batch_size=500)
        
    @classmethod
    def cancel_order(self, user, order_id):
        try:
            with transaction.atomic():
                order = Orders.objects.filter(id=order_id, user=user).select_for_update().first()
                if not order:
                    error = Exception('Order not found')
                    error.status = status.HTTP_404_NOT_FOUND
                    raise error
                if order.status >= Orders.SHIPPED:
                    error = Exception(f'Order is already {order.STATUS_CHOICES[order.status][1]}')
                    error.status = status.HTTP_400_BAD_REQUEST
                    raise error
                order.status = Orders.CANCELLED
                order.save(update_fields=['status'])
        except Exception as e:
            if hasattr(e, 'status'):
                raise e
            else:
                error = Exception('Something went wrong')
                error.status = status.HTTP_500_INTERNAL_SERVER_ERROR
                print("Error while canceling order:", e)
                raise error
    
    @classmethod
    def return_items_to_cart(self, order, user):
        order_items = OrdersItems.objects.filter(order=order).only('product_variant', 'quantity').select_related('product_variant')
        cart_items = []
                    
        for item in order_items:
            if item.product_variant is None:
                continue
            cart_items.append(
                Cart(
                    user=user, 
                    product_variant=item.product_variant, 
                    quantity=min(item.quantity, item.product_variant.quantity)
                )
            )
        Cart.objects.bulk_create(cart_items, batch_size=500)