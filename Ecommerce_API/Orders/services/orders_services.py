from ..models import Orders, OrdersItems
from cart.models import CartItem, Cart
from django.db import transaction
from products.models import ProductVariant
from rest_framework import status
from orders.queryset import CreateOrderQueryset
from coupons.models import CouponRule
from orders.models import OrderCoupons
import json

class OrdersServices:
    @classmethod
    def create_order(self, user, address, coupons=None):
        
        try:
            cartItems = CreateOrderQueryset.get_cart_items(user)
            cart = Cart.objects.filter(user=user).first()
            if len(list(cartItems)) == 0:
                return None

            total_price = sum([item.product_variant.price * item.quantity for item in cartItems])
            
            with transaction.atomic():
                
                order = Orders.objects.create(user=user, total_price=total_price, discount_price=cart.discount_price, address=address)
                
                order_items = {}
                variants = []
                coupon_order_relations = []
                for cp in coupons.values() if coupons else []:
                    if isinstance(cp, dict):
                        for c in cp.values():
                            coupon_order_relations.append(OrderCoupons(coupon_id=c['id'], order_id=order.id))
                    else:
                        for c in cp:
                            coupon_order_relations.append(OrderCoupons(coupon_id=c['id'], order_id=order.id))
                            
                OrderCoupons.objects.bulk_create(coupon_order_relations, batch_size=500, ignore_conflicts=True)

                OrderServicesHelpers.create_order_items_objects(cartItems, order, order_items, variants)
                OrderServicesHelpers.update_product_variant_quantity(variants, order_items, user)

                OrdersItems.objects.bulk_create(order_items.values())
                CartItem.objects.filter(user=user).delete()
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
                CartItem.objects.filter(user=user).delete()
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
                CartItem(
                    user=user, 
                    product_variant=item.product_variant, 
                    quantity=min(item.quantity, item.product_variant.quantity)
                )
            )
        CartItem.objects.bulk_create(cart_items, batch_size=500)
        
        

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
                CartItem.objects.filter(user_id=user.id, product_variant_id=product.id).update(
                    quantity=product.quantity + order_items.get(f'{product.id}').quantity
                )
                e = Exception("Not enough items in stock!")
                e.status_code = 400
                raise e
        ProductVariant.objects.bulk_update(products, ['quantity'], batch_size=500)
        
    @classmethod
    def calculate_discount_price(cls, user, cart):
        cartItems = cart.cartitem.all()
        total_price = cart.total_price
        coupons = CreateOrderQueryset.get_coupons(user, total_price, cart)
        coupon_types = coupons['coupons']
        codes = set(coupons['codes']) 
        
        expired_coupons = []
        
        coupons = {}
        for t in coupon_types:
            coupons[t['couponrule__coupon_type']] = t['coupons']
            if t['couponrule__coupon_type'] == CouponRule.COUPON_TYPE_PRODUCT:
                c = {}
                for cp in coupons[t['couponrule__coupon_type']]:
                    c[cp['product_id']] = cp
                coupons[t['couponrule__coupon_type']] = c
            if t['couponrule__coupon_type'] == CouponRule.COUPON_TYPE_SELLER:
                c = {}
                for cp in coupons[t['couponrule__coupon_type']]:
                    c[cp['seller_id']] = cp
                coupons[t['couponrule__coupon_type']] = c
        
        total_price = 0
        for i, item in enumerate(cartItems): 
            # Product Coupons
            coupon = coupons.get(CouponRule.COUPON_TYPE_PRODUCT)
            if coupon and coupon.get(item.product_variant.parent_id):
                coupon = coupon.get(item.product_variant.parent_id)
                coupon['uses'] = coupon.get('uses', 0) + item.quantity
                if coupon['discount_type'] == CouponRule.DISCOUNT_TYPE_FIXED:
                    cartItems[i].product_variant.price = max(item.product_variant.price - coupon['discount_value'], 0)
                elif coupon['discount_type'] == CouponRule.DISCOUNT_TYPE_PERCENTAGE:
                    cartItems[i].product_variant.price =  item.product_variant.price - min(
                        (item.product_variant.price * (float(cp['discount_value'])/100)), 
                        cp.get('discount_limit') or 9999999
                    )
                codes.remove(coupon['code'])
            
            # Seller Coupons
            coupon = coupons.get(CouponRule.COUPON_TYPE_SELLER)
            if coupon and coupon.get(item.product_variant.seller_id):
                coupon = coupon.get(item.product_variant.seller_id)
                coupon['uses'] = coupon.get('uses', 0) + item.quantity
                if coupon['rule_type'] == CouponRule.RULE_TYPE_MIN_PRODUCT_PRICE and item.product_variant.price < coupon['rule_value']:
                    continue
                if coupon['discount_type'] == CouponRule.DISCOUNT_TYPE_FIXED:
                    cartItems[i].product_variant.price = max(item.product_variant.price - coupon['discount_value'], 0)
                elif coupon['discount_type'] == CouponRule.DISCOUNT_TYPE_PERCENTAGE:
                    cartItems[i].product_variant.price =  item.product_variant.price - min(
                        (item.product_variant.price * (float(cp['discount_value'])/100)), 
                        cp.get('discount_limit') or 9999999
                    )
                codes.remove(coupon['code'])
            
            total_price += item.product_variant.price * item.quantity
            
        # Apply order coupons
        for cp in coupons.get(CouponRule.COUPON_TYPE_ORDER, []):
            if cp['discount_type'] == CouponRule.DISCOUNT_TYPE_FIXED:
                total_price = max(total_price - cp['discount_value'], 0)
            elif cp['discount_type'] == CouponRule.DISCOUNT_TYPE_PERCENTAGE:
                total_price -= min((total_price * (float(cp['discount_value'])/100)), cp.get('discount_limit') or 9999999)
            codes.remove(cp['code'])
                
        return {'discount_price': total_price, 'expired_coupons': list(codes)}
        