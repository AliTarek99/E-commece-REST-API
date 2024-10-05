from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.response import Response
from rest_framework import status
from ..models import Orders, OrdersItems
from ..serializers import OrdersSerializer, PaymobCallbackSerializer, CreateOrderSerializer
from rest_framework.permissions import IsAuthenticated
from orders.services import PaymobServices, OrdersServices
from django.db.models import Prefetch, OuterRef
from products.models import ProductImages


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
            orders = Orders.objects.filter(id=order_id, user=request.user.id).prefetch_related(
                Prefetch('order_items', queryset=OrdersItems.objects.prefetch_related(
                    Prefetch('product_images', queryset=ProductImages.objects.filter(created_at__lt=OuterRef('orders.created_at')))
                    )
                )
            ).first()
        return Response(orders, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = CreateOrderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order = OrdersServices.create_order(request.user)
        PaymobServices.create_intention(
            amount=order.total_price, 
            currency='EGP', 
            items=order.orderItems, 
            biling_data=serializer.data, 
            customer_data=request.user, 
            order_id=order.id
        )
        return Response(status=status.HTTP_201_CREATED)
    
    
class PaymentCallbackAPIs(APIView):
    def post(self, request):
        serializer = PaymobCallbackSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.update()
        return Response(status=status.HTTP_200_OK)