from django.db.models import OuterRef, Subquery, Value, F
from django.db.models.functions import JSONObject
from django.contrib.postgres.aggregates import ArrayAgg
from ..models import Orders, OrdersItems

class OrdersQueryset:
    @classmethod
    def get_order_by_id_queryset(cls, request, order_id):
        order_items_subquery = OrdersItems.objects.filter(order_id=OuterRef('pk')).annotate(
                item_json=JSONObject(
                    product_id=F('product_id'),
                    product_name=F('product__name'),
                    quantity=F('quantity'),
                    price=F('price')
                )
            ).values('item_json')
        orders = (
                Orders.objects.filter(id=order_id, user=request.user.id).annotate(
                    items=ArrayAgg(order_items_subquery, distinct=True)
                ).values('id', 'created_at', 'total_price', 'items', 'address')
            )
        return orders