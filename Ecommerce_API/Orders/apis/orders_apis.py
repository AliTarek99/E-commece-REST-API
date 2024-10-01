from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.response import Response
from rest_framework import status
from ..models import Orders, OrdersItems
from ..serializers import OrdersSerializer, OrderItemsSerializer
from rest_framework.permissions import IsAuthenticated
from ..services import OrdersServices
from orders.queryset import OrdersQueryset

class OrdersAPIs(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get(self, request):
        order_id = request.query_params.get('order_id')
        orders = None
        if not order_id:
            orders = Orders.objects.filter(user=request.user.id).only('id', 'user', 'created_at', 'total_price').order_by('-created_at').all()
            serializer = OrdersSerializer(list(orders), many=True)
            
            orders = serializer.data
        else:
            orders = OrdersQueryset.get_order_by_id_queryset(request=request, order_id=order_id)
        return Response(orders, status=status.HTTP_200_OK)

    def post(self, request):
        OrdersServices.create_order(request.user)
        return Response(status=status.HTTP_201_CREATED)