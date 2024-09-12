from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.response import Response
from rest_framework import status
from ..models import Orders
from ..serializers import OrdersSerializer, OrderItemsSerializer
from rest_framework.permissions import IsAuthenticated
from ..queryset import orders_queryset

class OrdersAPIs(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get(self, request):
        order_id = request.query_params.get('order_id')
        orders = None
        if not order_id:
            orders = Orders.objects.filter(user=request.user).only('id', 'user', 'order_date', 'total_price').order_by('-order_date')
        orders = Orders.objects.filter(id=order_id).prefetch_related('orders_items').only(
            'id', 
            'user', 
            'order_date', 
            'total_price', 
            'orders_items__product', 
            'orders_items__quantity', 
            'orders_items__price'
        )
        serializer = OrdersSerializer(orders, many=True)
        return Response(serializer.data)

    def post(self, request):
        orders_queryset.create_order(request.user)
        return Response(status=status.HTTP_201_CREATED)