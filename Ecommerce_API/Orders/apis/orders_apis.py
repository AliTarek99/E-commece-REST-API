from rest_framework.views import APIView
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.response import Response
from rest_framework import status
from ..models import Orders
from ..serializers import OrdersSerializer, PaymobCallbackSerializer, CreateOrderSerializer, OrdersListSerializer
from orders.services import PaymobServices, OrdersServices
from orders.queryset import ReportQueryset


class GetOrdersListAPIs(ListAPIView):
    serializer_class = OrdersListSerializer
    ordering = ['-created_at']

    def get_queryset(self):
        return Orders.objects.filter(user=self.request.user.id).only(
            'id', 
            'user', 
            'created_at', 
            'total_price',
            'address',
            'status'
        ).select_related('address').order_by('-created_at')
    
class GetOrderDetailsAPIs(RetrieveAPIView):
    serializer_class = OrdersSerializer
    lookup_field = 'id'
    
    def get_queryset(self):
        return Orders.objects.filter(user=self.request.user.id).prefetch_related('orders_items')



class OrdersAPIs(APIView):

    def post(self, request):
        serializer = CreateOrderSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        try:
            order = OrdersServices.create_order(
                request.user, 
                address=serializer.validated_data.get('address')
            )
            if not order:
                return Response({'error': 'Order not created'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status= e.status_code if hasattr(e, 'status_code') else status.HTTP_500_INTERNAL_SERVER_ERROR)
        try:
            payment_url = PaymobServices.create_intention(
                amount=order.total_price, 
                currency='EGP', 
                biling_data=serializer.data, 
                customer_data=request.user, 
                order_id=order.id,
            )
        except Exception as e:
            OrdersServices.restore_items(order, user=request.user)
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(payment_url, status=status.HTTP_201_CREATED)
    
    
class SalesReportAPI(APIView):
    def get(self, request):
        report = ReportQueryset.get_report_queryset()
        return Response(report, status=status.HTTP_200_OK)

    

class ReorderAPI(APIView):
    def post(self, request):
        if not request.data.get('order_id'):
            return Response({'error': 'Order ID is required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            OrdersServices.reorder(request.user, request.data.get('order_id'))
        except Exception as e:
            return Response({'error': str(e)}, status=e.status if hasattr(e, 'status') else status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(status=status.HTTP_200_OK)
   
    
class ReturnOrderAPI(APIView):
    def post(self, request):
        if not request.data.get('order_id'):
            return Response({'error': 'Order ID is required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            OrdersServices.return_order(request.user, request.data.get('order_id'))
        except Exception as e:
            return Response({'error': str(e)}, status=e.status if hasattr(e, 'status') else status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(status=status.HTTP_200_OK)
    
    
class PaymentCallbackAPIs(APIView):
    def post(self, request):
        # serializer = PaymobCallbackSerializer(data=request.data, context={'request': request})
        # serializer.is_valid(raise_exception=True)
        print('in callback', request.data)
        if request.data.get('success'):
            # serializer.update()
            return Response(status=status.HTTP_200_OK)
        else:
            # after validation merchant_order_id field contains the whole order not just the id
            # OrdersServices.restore_items(serializer.data.get('merchant_order_id'))
            return Response(status=status.HTTP_200_OK)