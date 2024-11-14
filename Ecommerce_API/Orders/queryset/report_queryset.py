from orders.models import Orders, OrdersItems
from django.db.models import Sum, Avg, Subquery, OuterRef, F, ExpressionWrapper, DecimalField, Count, Func, Value
from django.db.models.functions import TruncWeek
from django.db import connection, transaction
from django.contrib.postgres.fields import JSONField, CITextField


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