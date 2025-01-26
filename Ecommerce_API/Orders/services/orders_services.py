from ..models import Orders, OrdersItems
from cart.models import CartItem, Cart, CartCoupon
from django.db import transaction
from products.models import ProductVariant
from rest_framework import status
from orders.queryset import CreateOrderQueryset
from orders.models import OrderCoupons
from coupons.services import CouponServices
from django.db.models import Prefetch
import constants
from orders.models import ReturnItem, ReturnRequest
from orders.services.paymob_services import PaymobServices



class OrdersServices:
    @classmethod
    def create_order(cls, user, address):
        
        try:
            cart = Cart.objects.filter(user=user).prefetch_related(Prefetch('cartcoupon', queryset=CartCoupon.objects.select_related('coupon'))).first()
            cartItems = CreateOrderQueryset.get_cart_items(cart)
            if len(list(cartItems)) == 0:
                return None

            total_price = sum([item.product_variant.price * item.quantity for item in cartItems])
            
            result = CouponServices.calculate_discount_price(user, cart)
            if len(result['expired_coupons']):
                cart.discount_price = result['discount_price']
                cart.save()
                error = Exception('Expired Coupons')
                error.expired_coupons = result['expired_coupons']
                error.status = status.HTTP_400_BAD_REQUEST
                raise error
        
            with transaction.atomic():
                order = Orders.objects.create(user=user, total_price=total_price, discount_price=result['discount_price'], address=address)
                
                order_items = {}
                variants = []
                coupon_order_relations = []
                codes = []
                for cp in cart.cartcoupon.all():
                    codes.append(cp.coupon.code)
                    coupon_order_relations.append(OrderCoupons(coupon_id=cp.coupon.id, order_id=order.id))
                    
                
                OrderCoupons.objects.bulk_create(coupon_order_relations, batch_size=500, ignore_conflicts=True)
                
                # Decrease stock
                OrderServicesHelpers.update_product_variant_quantity(variants, order_items, user)

                # Add orderItems objects
                OrderServicesHelpers.create_order_items_objects(cartItems, order, order_items, variants)
                
                # Add order items to database
                OrdersItems.objects.bulk_create(order_items.values())
                
                # Empty the cart
                CartItem.objects.filter(cart=cart).delete()
                
                # Update Coupon Uses
                CouponServices.use_coupons(user, codes)
                
                # delete cart coupons
                CartCoupon.objects.filter(cart=cart).delete()
                cart.total_price = 0
                cart.discount_price = 0
                
                # Save cart changes
                cart.save(update_fields=['total_price', 'discount_price'])
                
                return order
        except Exception as e:
            if hasattr(e, 'status'):
                raise e
            else:
                print(e)
                raise Exception("Something went wrong!")
        
    @classmethod
    def restore_items(cls, order, user):
        with transaction.atomic():
            coupons = order.order_coupons.select_related('coupon').all()
            cart_coupon = []
            codes = []
            for coupon in coupons:
                codes.append(coupon.coupon.code)
                cart_coupon.append(CartCoupon(coupon=coupon.coupon, cart=user.cart))
                
            CartCoupon.objects.bulk_create(cart_coupon, batch_size=500, ignore_conflicts=True)
            CouponServices.unuse_coupons(user, codes)
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
                CartItem.objects.filter(cart_id=user.id).delete()
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
    def return_order_items(cls, user, order, items, reason):
        try:
            with transaction.atomic():
                request = ReturnRequest.objects.create(order=order, user=user, reason=reason)
                return_items = []
                for item in items:
                    return_items.append(ReturnItem(return_request=request, product_variant=item['product_variant'], quantity=item['quantity'], price=item['price']))
                ReturnItem.objects.bulk_create(return_items, batch_size=500)
        except Exception as e:
            if hasattr(e, 'status'):
                raise e
            else:
                error = Exception('Something went wrong')
                error.status = status.HTTP_500_INTERNAL_SERVER_ERROR
                print("Error while returning order:", e)
                raise error
          
    @classmethod
    def return_items_to_stock(cls, order=None, order_items=None):
        if order_items is None:
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
    def cancel_order(cls, user, order_id):
        try:
            with transaction.atomic():
                order = Orders.objects.filter(id=order_id, user=user).select_related('coupon').select_for_update().first()
                if not order:
                    error = Exception('Order not found')
                    error.status = status.HTTP_404_NOT_FOUND
                    raise error
                if order.status >= constants.ORDER_SHIPPED:
                    error = Exception(f'Order is already {order.STATUS_CHOICES[order.status][1]}')
                    error.status = status.HTTP_400_BAD_REQUEST
                    raise error
                order.status = constants.ORDER_CANCELLED
                order.save(update_fields=['status'])
                
                CouponServices.unuse_coupons(user, order.ordercoupons.all().values_list('coupon__code', flat=True))
        except Exception as e:
            if hasattr(e, 'status'):
                raise e
            else:
                error = Exception('Something went wrong')
                error.status = status.HTTP_500_INTERNAL_SERVER_ERROR
                print("Error while canceling order:", e)
                raise error
    
    @classmethod
    def return_items_to_cart(cls, order, user):
        order_items = OrdersItems.objects.filter(order=order).only('product_variant', 'quantity').select_related('product_variant')
        cart_items = []
        cart = Cart.objects.filter(user=user).first()
                    
        for item in order_items:
            if item.product_variant is None:
                continue
            cart_items.append(
                CartItem(
                    cart=cart, 
                    product_variant=item.product_variant, 
                    quantity=min(item.quantity, item.product_variant.quantity),
                    discount_price=item.discount_price
                )
            )
        CartItem.objects.bulk_create(cart_items, batch_size=500)
        CouponServices.calculate_discount_price(user, cart)
    
    @classmethod
    def return_request_decision(cls, request_id, decision):
        try:
            with transaction.atomic():
                request = ReturnRequest.objects.filter(
                    id=request_id, 
                    status=constants.RETURN_CHECKING_PACKAGE
                ).select_related('order').prefetch_related('return_items').select_for_update().first()
                if not request:
                    error = Exception('Return request not found')
                    error.status = status.HTTP_404_NOT_FOUND
                    raise error
                if decision == constants.RETURN_APPROVED:
                    request.status = constants.RETURN_APPROVED
                    request.save(update_fields=['status'])
                    request.order.status = constants.ORDER_RETURNED
                    request.order.save(update_fields=['status'])
                    cls.return_items_to_stock(request.order)
                    amount = 0
                    
                    for item in request.return_items.all():
                        print("here1")
                        amount += item.price * item.quantity
                    PaymobServices.refund_payment(amount + request.order.shipping_price * 2, request.order)
                else:
                    request.status = constants.RETURN_REJECTED
                    request.save(update_fields=['status'])
        except Exception as e:
            if hasattr(e, 'status'):
                raise e
            else:
                error = Exception('Something went wrong')
                error.status = status.HTTP_500_INTERNAL_SERVER_ERROR
                print("Error while processing return request:", e)
                raise error
        
        

class OrderServicesHelpers:
    @classmethod
    def create_order_items_objects(cls, cart, order, order_items, variants):
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
                image_url=item.default_image,
                discount_price=item.discount_price
            )
            order_items[f'{order_item.product_variant_id}'] = order_item
            variants.append(item.product_variant_id)
            
    @classmethod
    def update_product_variant_quantity(cls, variants, order_items, user):
        products = ProductVariant.objects.filter(id__in=variants).select_for_update().all()
        for product in products:
            product.quantity = product.quantity - order_items.get(f'{product.id}').quantity
            if product.quantity < 0:
                CartItem.objects.filter(cart_id=user.id, product_variant_id=product.id).update(
                    quantity=product.quantity + order_items.get(f'{product.id}').quantity
                )
                e = Exception("Not enough items in stock!")
                e.status = 400
                raise e
        ProductVariant.objects.bulk_update(products, ['quantity'], batch_size=500)
        