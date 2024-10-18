from ..models import Orders, OrdersItems
from cart.models import Cart
from django.db import transaction
from products.models import ProductVariant, ProductImages
from django.db.models import OuterRef, Subquery
from django.contrib.postgres.aggregates import ArrayAgg


class OrdersServices:
    @classmethod
    def create_order(self, user):
        
        try:
            cart = Cart.objects.filter(user=user).only(
                'user_id', 
                'product_variant_id', 
                'quantity', 'product_variant__size', 
                'product_variant__price',
                'product_variant__color', 
                'product_variant__parent__name',
                'product_variant__parent__seller_id', 
                'product_variant__parent__seller__name',
                'product_variant__parent__description',
            ).annotate(
                images=Subquery(
                    ProductImages.objects.filter(
                        product_id=OuterRef('product_variant__parent_id'),
                        color=OuterRef('product_variant__color')
                    ).values('product_id').annotate(
                        image_urls=ArrayAgg('url')
                    ).values('image_urls')
                )
            ).all()
            
            if len(list(cart)) == 0:
                return False, False

            total_price = sum([item.product_variant.price * item.quantity for item in cart])
            
            with transaction.atomic():
                order = Orders.objects.create(user=user, total_price=total_price)

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

                orderItems = OrdersItems.objects.bulk_create(order_items.values())
                Cart.objects.filter(user_id=user.id).delete()
                return order, orderItems
        except Exception as e:
            if hasattr(e, 'status_code'):
                raise e
            else:
                print(e)
                raise Exception("Something went wrong!")
        
    @classmethod
    def restore_items(cls, order):
        order_items = OrdersItems.objects.filter(order=order)
        cart_items = []
        for item in order_items:
            cart_item = Cart(
                user=item.order.user,
                product_variant=item.product_variant,
                quantity=item.quantity,
                size=item.size
            )
            cart_items.append(cart_item)
        Cart.objects.bulk_create(cart_items)
        order.delete()