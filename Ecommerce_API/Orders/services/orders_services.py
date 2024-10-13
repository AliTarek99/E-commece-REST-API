from ..models import Orders, OrdersItems
from cart.models import Cart
from django.db import transaction
from products.models import ProductVariantSizes
from django.db.models import Q, OuterRef, Subquery


class OrdersServices:
    @classmethod
    def create_order(self, user):
        with transaction.atomic():
            try:
                cart = Cart.objects.filter(user=user).only(
                    'user_id', 
                    'product_variant_id', 
                    'quantity', 'size', 
                    'product_variant__color', 
                    'product_variant__parent__name',
                    'product_variant__parent__seller_id', 
                    'product_variant__parent__seller__name',
                    'product_variant__parent__description',
                ).prefetch_related('product_variant__productimages_set').annotate(
                    price=Subquery(ProductVariantSizes.objects.filter(size=OuterRef('size'), product_variant_id=OuterRef('product_variant_id')).values('price')[:1])
                ).all()
                
                if len(list(cart)) == 0:
                    return False, False

                total_price = sum([item.price * item.quantity for item in cart])
                order = Orders.objects.create(user=user, total_price=total_price)

                order_items = {}
                condition = Q()   
                for item in cart:
                    order_item = OrdersItems(
                        order=order,
                        product_variant_id=item.product_variant_id,
                        quantity=item.quantity,
                        price=item.price,
                        size=item.size,
                        description=item.product_variant.parent.description,
                        color=item.product_variant.color,
                        name=item.product_variant.parent.name,
                        seller_id=item.product_variant.parent.seller_id,
                    )
                    order_items[f'{order_item.product_variant_id}'] = order_item
                    print(order_item.product_variant_id, order_items[f'{order_item.product_variant_id}'])
                    condition |= Q(product_variant_id=item.product_variant_id) & Q(size=item.size)
                
                products = ProductVariantSizes.objects.filter(condition).select_for_update().all()
                print(list(products), '-' * 500, order_items.values())
                for product in products:
                    product.quantity = product.quantity - order_items.get(f'{product.product_variant_id}').quantity
                ProductVariantSizes.objects.bulk_update(products, ['quantity'])

                orderItems = OrdersItems.objects.bulk_create(order_items.values())
                Cart.objects.filter(user_id=user.id).delete()
                return order, orderItems
            except Exception as e:
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