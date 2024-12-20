from orders.models import Orders, OrdersItems
from django.db.models import Sum, Avg, Subquery, OuterRef, F, ExpressionWrapper, DecimalField, Count, Func, Value, Q
from django.db.models.functions import TruncWeek
from django.db import connection, transaction
from django.contrib.postgres.fields import JSONField, CITextField
from cart.models import CartItem, CartCoupon
from products.models import ProductVariant, ProductImages
from django.db.models.functions import Coalesce
from django.contrib.postgres.aggregates import JSONBAgg
from coupons.models import Coupon, CouponRule
from django.utils.timezone import now


class ReportQueryset():
    @classmethod
    def get_report_queryset(cls):
        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ;")
                res = Orders.objects.annotate(
                    week=TruncWeek('created_at')
                ).values('week', 'orders_items__seller_id').annotate(
                    total_sales=Sum(
                        ExpressionWrapper(
                            F('orders_items__quantity') * F('orders_items__price'),
                            output_field=DecimalField()
                        )
                    ),
                    max_product=Subquery(
                        cls.get_seller_sold_items(OuterRef('orders_items__seller_id'), ordering='-price')[:1],
                        output_field=JSONField()
                    ),
                    average_product_price=Avg('orders_items__price'),
                    min_product_price=Subquery(
                        cls.get_seller_sold_items(OuterRef('orders_items__seller_id'), ordering='price')[:1],
                        output_field=JSONField()
                    ),
                    order_count=Count('id')
                )
                return list(res)
        
    @classmethod
    def get_seller_sold_items(cls, seller, ordering='price', fields=['price']):
        return OrdersItems.objects.filter(
            seller_id=seller
        ).order_by(ordering).annotate(
            product=Func(
                Value('name'), 
                F('name'),
                Value('price'),
                F('price'),
                function='jsonb_build_object',
                output_field=CITextField()
            )    
        ).values('product')
        
    
class CreateOrderQueryset():
    @classmethod
    def get_cart_items(cls, cart):
        return CartItem.objects.filter(cart=cart).only(
                'cart_id',  
                'quantity', 
                'product_variant',
                'discount_price'
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
            
    @classmethod
    def get_coupons(cls, user, total_price, cart):
        codes = CartCoupon.objects.filter(cart=cart).select_related('coupon').values_list('coupon__code', flat=True)
        coupons = Coupon.objects.filter(
            code__in=codes,
            is_active=True,
            couponrule__expires_at__gte=now()
        ).filter(
            Q(couponuse__user=user) | Q(couponuse__user__isnull=True)
        ).filter(
            Q(couponuse__uses__isnull=True) | Q(couponuse__uses__lt=Coalesce(F('couponrule__max_uses_per_user'), 999999999))
        ).filter(
            (
                Q(couponrule__coupon_type=CouponRule.COUPON_TYPE_ORDER) & 
                Q(couponrule__rule_type=CouponRule.RULE_TYPE_MIN_ORDER_TOTAL_PRICE) & 
                Q(couponrule__rule_value__lte=total_price)
            ) | Q(couponrule__rule_type__isnull=True) | Q(couponrule__rule_type=CouponRule.RULE_TYPE_MIN_PRODUCT_PRICE)
        ).distinct().prefetch_related(
            'couponuse',
            'couponproduct'
        ).select_related('couponrule').values('couponrule__coupon_type').annotate(
            coupons=JSONBAgg(
                Func(
                    Value('id'), F('id'),
                    Value('code'), F('code'),
                    Value('product_id'), F('couponproduct__product_id'),
                    Value('discount_type'), F('couponrule__discount_type'),
                    Value('discount_value'), F('couponrule__discount_value'),
                    Value('rule_type'), F('couponrule__rule_type'),
                    Value('rule_value'), F('couponrule__rule_value'),
                    Value('discount_limit'), F('couponrule__discount_limit'),
                    Value('seller_id'), F('seller_id'),
                    function='jsonb_build_object'
                )
            )
        )
        return {'coupons': coupons, 'codes': codes}