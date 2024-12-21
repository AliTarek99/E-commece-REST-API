from coupons.models import Coupon, CouponUse
from cart.models import CartItem, Cart, CartCoupon
from django.db import transaction
from django.db.models import F
from orders.queryset import CreateOrderQueryset
import constants

class CouponServices():
    @classmethod
    def apply_coupon(cls, user, coupon):
        products = []
        cart = Cart.objects.filter(user=user).prefetch_related('cartitem').first()
        with transaction.atomic():
            CartCoupon.objects.create(cart=cart, coupon=coupon) 
            result = cls.calculate_discount_price(user, cart)
            cart.discount_price = result['discount_price']
            
            cart.save()
            
            return result 
    
    @classmethod
    def use_coupons(cls, user, codes):
        cls.change_coupon_uses(user, codes, 1)
    
    @classmethod
    def unuse_coupons(cls, user, codes):
        cls.change_coupon_uses(user, codes, -1)
        
    @classmethod
    def change_coupon_uses(self, user, codes, uses):
        Coupon.objects.filter(code__in=codes).select_for_update().update(uses=F('uses') + uses)
        ## Update existing coupon uses
        query = CouponUse.objects.filter(user=user, coupon__code__in=codes).select_related('coupon')
        updatedUses = list(query)
        query.update(uses=F('uses') + uses)
        
        ## Check for new coupons being used
        if uses > 0:
            codes = set(codes)
            for use in updatedUses:
                codes.remove(use.coupon.code)
                
            coupon_use = []
            coupons = Coupon.objects.filter(code__in=list(codes))
            for coupon in coupons:
                coupon_use.append(CouponUse(user=user, coupon=coupon, uses = 1))
            
            CouponUse.objects.bulk_create(coupon_use, batch_size=500)
        
    @classmethod
    def calculate_discount_price(cls, user, cart):
        cartItems = cart.cartitem.all()
        coupons = CreateOrderQueryset.get_coupons(user, cart.total_price, cart)
        coupon_types = coupons['coupons']
        codes = set(coupons['codes']) 
        
        
        coupons = {}
        for t in coupon_types:
            coupons[t['couponrule__coupon_type']] = t['coupons']
            if t['couponrule__coupon_type'] == constants.COUPON_TYPE_PRODUCT:
                c = {}
                for cp in coupons[t['couponrule__coupon_type']]:
                    c[cp['product_id']] = cp
                coupons[t['couponrule__coupon_type']] = c
            if t['couponrule__coupon_type'] == constants.COUPON_TYPE_SELLER:
                c = {}
                for cp in coupons[t['couponrule__coupon_type']]:
                    c[cp['seller_id']] = cp
                coupons[t['couponrule__coupon_type']] = c
        
        discount_price = 0
        for i, item in enumerate(cartItems): 
            # Product Coupons
            coupon = coupons.get(constants.COUPON_TYPE_PRODUCT)
            if coupon and coupon.get(item.product_variant.parent_id):
                coupon = coupon.get(item.product_variant.parent_id)
                if coupon['discount_type'] == constants.DISCOUNT_TYPE_FIXED:
                    cartItems[i].discount_price = max(item.discount_price - coupon['discount_value'], 0)
                elif coupon['discount_type'] == constants.DISCOUNT_TYPE_PERCENTAGE:
                    cartItems[i].discount_price =  max(item.discount_price - min(
                        (item.product_variant.price * (float(cp['discount_value'])/100)), 
                        cp.get('discount_limit') or 9999999
                    ), 0)
                codes.remove(coupon['code'])
            
            # Seller Coupons
            coupon = coupons.get(constants.COUPON_TYPE_SELLER)
            if coupon and coupon.get(item.product_variant.seller_id):
                coupon = coupon.get(item.product_variant.seller_id)
                if coupon['minimum_required_value'] and item.product_variant.price < coupon['minimum_required_value']:
                    continue
                if coupon['discount_type'] == constants.DISCOUNT_TYPE_FIXED:
                    cartItems[i].discount_price = max(item.discount_price - coupon['discount_value'], 0)
                elif coupon['discount_type'] == constants.DISCOUNT_TYPE_PERCENTAGE:
                    cartItems[i].discount_price =  max(item.discount_price - min(
                        (item.product_variant.price * (float(cp['discount_value'])/100)), 
                        cp.get('discount_limit') or 9999999
                    ), 0)
                codes.remove(coupon['code'])
            discount_price += item.discount_price * item.quantity
        
        CartItem.objects.bulk_update(cartItems, ['discount_price'])
        # Apply order coupons
        for cp in coupons.get(constants.COUPON_TYPE_ORDER, []):
            if cp['discount_type'] == constants.DISCOUNT_TYPE_FIXED:
                discount_price = max(discount_price - cp['discount_value'], 0)
            elif cp['discount_type'] == constants.DISCOUNT_TYPE_PERCENTAGE:
                discount_price -= min((discount_price * (float(cp['discount_value'])/100)), cp.get('discount_limit') or 9999999)
            codes.remove(cp['code'])
        
        if len(codes):
            CartCoupon.objects.filter(cart=cart, coupon__code__in=codes).delete()
            result = cls.calculate_discount_price(user, cart)
            discount_price = result['discount_price']
            codes = list(codes) + result['expired_coupons']
            
                
        return {'discount_price': discount_price, 'expired_coupons': list(codes), 'items_prices': [{'id': item.product_variant.id, 'discount_price': item.discount_price} for item in cartItems]}
    
    @classmethod
    def remove_cart_coupon(cls, user, code):
        cart_coupon = CartCoupon.objects.filter(coupon__code=code, cart_id=user.id).select_related('cart', 'coupon').first()
        cart_coupon.delete()
        result = cls.calculate_discount_price(user, cart_coupon.cart)
        cart_coupon.cart.discount_price = result['discount_price']
        cart_coupon.cart.save(update_fields=['discount_price'])
        return result