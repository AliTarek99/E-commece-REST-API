from products.models import ProductVariant
from ..serializers import CartItemSerializer
from cart.models import CartItem, CartCoupon, Cart
from rest_framework import status
from django.db import transaction
from django.utils import timezone
from django.db.models import F
from coupons.services import CouponServices
from coupons.models import CouponRule

class CartServices():
    @classmethod
    def add_product_to_cart(cls, request):
        try:
            cart = Cart.objects.filter(user=request.user).first()
            product = ProductVariant.objects.filter(id=request.data['product_variant']).first()
            if not product:
                error = Exception('Product not found')
                error.status = status.HTTP_404_NOT_FOUND
                raise error
            with transaction.atomic():
                # lock the cart item
                cart_product = CartItem.objects.select_for_update().filter(
                    cart=cart, 
                    product_variant=request.data['product_variant']
                ).first()
                
                #get coupons that apply to this product
                coupons = CartCoupon.objects.filter(
                    cart=cart, 
                    coupon__couponproduct__product=product.parent,
                    coupon__is_active=True,
                    coupon__couponrule__expires_at__gte=timezone.now(),
                    coupon__couponrule__max_uses_per_user__lt=F('coupon__couponuse__uses')
                ).select_related('coupon__couponrule', 'coupon')
                        
                # update cart item if it exists
                serializer = CartItemSerializer(cart_product, data={
                        'cart': cart.user_id,
                        'quantity': request.data['quantity'] + (cart_product.quantity if cart_product else 0),
                        'discount_price': product.price
                    }, context={'user': request.user, 'product_variant': product}
                )
                
                # Save Cart Item
                if not serializer.is_valid():
                    error = Exception(serializer.errors)
                    error.status = status.HTTP_400_BAD_REQUEST
                    raise error
                serializer.save()
            
                # Re-calculate discount price
                cart.total_price += product.price * request.data['quantity']
                
                result = CouponServices.calculate_discount_price(user=request.user, cart=cart)
                cart.discount_price = result['discount_price']
                cart.save(update_fields=['discount_price', 'total_price'])
                
                discount_price = 0
                for item in result['items_prices']:
                    print
                    if item['id'] == product.id:
                        discount_price = item['discount_price']
                        break
                
                return {
                    'discount_price': cart.discount_price,
                    'total_price': cart.total_price,
                    'product_discount_price': discount_price,
                    'expired_coupons': result['expired_coupons'],
                    'quantity': serializer.validated_data['quantity']
                }
        except Exception as e:
            if hasattr(e, 'status'):
                raise e
            else:
                error = Exception('Something went wrong')
                error.status = status.HTTP_500_INTERNAL_SERVER_ERROR
                print("Error while adding product to cart:", e)
                raise error
            
    @classmethod
    def delete_cart_item(cls, request, product_variant):
        cart_product = CartItem.objects.filter(
            cart_id=request.user.id, 
            product_variant_id=product_variant
        ).select_related('product_variant__parent', 'product_variant').only(
            'user_id',
            'product_variant_id',
            'product_variant__parent_id',
            'product_variant__price'
            'quantity',
            'discount_price'
        ).first()
        with transaction.atomic():
            
            if not cart_product:
                error = Exception('Product not found')
                error.status = status.HTTP_404_NOT_FOUND
                raise error
                
            Cart.objects.filter(user=request.user).update(total_price=F('total_price') - cart_product.product_variant.price * cart_product.quantity)
            cart = Cart.objects.filter(user=request.user).first()
            

            cart_product.delete()
            # remove unused coupons
            unused_coupons = CartCoupon.objects.filter(
                cart=cart
            ).exclude(
                coupon__couponproduct__product__productvariant__cartitem__cart=cart
            )
            
            # get sellers that have products in cart
            sellers = [coupon.coupon.seller for coupon in unused_coupons]
            sellers = CartItem.objects.filter(product_variant__parent__seller__in=sellers).values_list('seller_id', flat=True)
            
            unused_coupons.exclude(coupon__seller_id__in=sellers)
            
            for coupon in unused_coupons:
                response['expired_coupons'].append(coupon.coupon.id)
            
            unused_coupons.delete()
            response = CouponServices.calculate_discount_price(user=request.user, cart=cart)
            cart.discount_price = response['discount_price']
            cart.save(update_fields=['discount_price'])
            return {
                'discount_price': cart.discount_price,
                'total_price': cart.total_price,
                'expired_coupons': response['expired_coupons']
            }