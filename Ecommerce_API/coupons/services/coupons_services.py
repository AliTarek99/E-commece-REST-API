from coupons.models import CouponRule, Coupon, CouponUse
from cart.models import CartItem, Cart, CartCoupon
from django.db import transaction
from django.db.models import F
from orders.queryset import CreateOrderQueryset

class CouponServices():
    @classmethod
    def apply_coupon(cls, user, coupon):
        products = []
        cart = Cart.objects.filter(user=user).prefetch_related('cartitem').first()
        
        ## Product Coupons
        if coupon.couponrule.coupon_type == CouponRule.COUPON_TYPE_PRODUCT:
            products = CartItem.objects.filter(
                user=user, 
                product_variant__parent__in=coupon.couponproduct.product_id,
            ).select_related('product_variant')
            
            for product in products:
                if coupon.couponrule.discount_type == CouponRule.DISCOUNT_TYPE_PERCENTAGE:
                    value_deducted = min(
                        product.discount_price * (coupon.couponrule.discount_value/100), 
                        coupon.couponrule.discout_limit if coupon.couponrule.discout_limit else 999999
                    )
                    product.discount_price -= value_deducted
                    cart.discount_price -= value_deducted
                elif coupon.couponrule.discount_type == CouponRule.DISCOUNT_TYPE_FIXED:
                    product.discount_price -= coupon.couponrule.discount_value 
                    cart.discount_price -= coupon.couponrule.discount_value
                    
        ## Seller Coupons
        elif coupon.couponrule.coupon_type == CouponRule.COUPON_TYPE_SELLER:
            products = CartItem.objects.filter(
                user=user,
                product_variant__parent__seller=coupon.seller
            ).select_related('product_variant')

            for product in products:
                if coupon.couponrule.discount_type == CouponRule.DISCOUNT_TYPE_PERCENTAGE:
                    value_deducted = min(
                        product.discount_price * (coupon.couponrule.discount_value/100), 
                        coupon.couponrule.discout_limit if coupon.couponrule.discout_limit else 999999
                    )
                    product.discount_price -= value_deducted
                    cart.discount_price -= value_deducted
                elif coupon.couponrule.discount_type == CouponRule.DISCOUNT_TYPE_FIXED:
                    product.discount_price -= coupon.couponrule.discount_value
                    cart.discount_price -= coupon.couponrule.discount_value
                    
        # save cart and used coupons
        with transaction.atomic():
            CartCoupon.objects.create(user=cart, coupon=coupon) 
            result = cls.calculate_discount_price(user, cart)
            cart.discount_price = result['discount_price']
            if len(result['expired_coupons']):
                CartCoupon.objects.filter(user=cart, coupon__code__in=result['expired_coupons']).delete()
            
            cart.save()
            
            return {
                'discount_price': cart.discount_price,
                'product_variants': [
                    {
                        'id': product.product_variant.id,
                        'discount_price': product.discount_price
                    } for product in products
                ],
                'expired_coupons': result['expired_coupons']
            } 
    
    @classmethod
    def use_coupons(cls, user, codes):
        cls.change_coupon_uses(user, codes, 1)
    
    @classmethod
    def unuse_coupons(cls, user, codes):
        cls.change_coupon_uses(user, codes, -1)
        
    @classmethod
    def change_coupon_uses(self, user, codes, uses):
        Coupon.objects.filter(code__in=codes).select_for_update().update(uses=F('uses') + uses)
        CouponUse.objects.filter(coupon__code__in=codes, user=user).select_for_update().update(uses=F('uses') + uses)
        
    @classmethod
    def calculate_discount_price(cls, user, cart):
        cartItems = cart.cartitem.all()
        discount_price = cart.total_price
        coupons = CreateOrderQueryset.get_coupons(user, discount_price, cart)
        coupon_types = coupons['coupons']
        codes = set(coupons['codes']) 
        
        
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
        
        discount_price = 0
        for i, item in enumerate(cartItems): 
            # Product Coupons
            coupon = coupons.get(CouponRule.COUPON_TYPE_PRODUCT)
            if coupon and coupon.get(item.product_variant.parent_id):
                coupon = coupon.get(item.product_variant.parent_id)
                coupon['uses'] = coupon.get('uses', 0) + item.quantity
                if coupon['discount_type'] == CouponRule.DISCOUNT_TYPE_FIXED:
                    cartItems[i].discount_price = max(item.discount_price - coupon['discount_value'], 0)
                elif coupon['discount_type'] == CouponRule.DISCOUNT_TYPE_PERCENTAGE:
                    cartItems[i].discount_price =  item.discount_price - min(
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
                    cartItems[i].discount_price = max(item.discount_price - coupon['discount_value'], 0)
                elif coupon['discount_type'] == CouponRule.DISCOUNT_TYPE_PERCENTAGE:
                    cartItems[i].discount_price =  item.discount_price - min(
                        (item.product_variant.price * (float(cp['discount_value'])/100)), 
                        cp.get('discount_limit') or 9999999
                    )
                codes.remove(coupon['code'])
            print(item.discount_price, item.quantity)
            discount_price += item.discount_price * item.quantity
            
        # Apply order coupons
        for cp in coupons.get(CouponRule.COUPON_TYPE_ORDER, []):
            if cp['discount_type'] == CouponRule.DISCOUNT_TYPE_FIXED:
                discount_price = max(discount_price - cp['discount_value'], 0)
            elif cp['discount_type'] == CouponRule.DISCOUNT_TYPE_PERCENTAGE:
                discount_price -= min((discount_price * (float(cp['discount_value'])/100)), cp.get('discount_limit') or 9999999)
            codes.remove(cp['code'])
        
        if len(codes):
            CartCoupon.objects.filter(user=cart, coupon__code__in=codes).delete()
            result = cls.calculate_discount_price(user, cart)
            discount_price = result['discount_price']
            codes = list(codes) + result['expired_coupons']
            
                
        return {'discount_price': discount_price, 'expired_coupons': list(codes)}