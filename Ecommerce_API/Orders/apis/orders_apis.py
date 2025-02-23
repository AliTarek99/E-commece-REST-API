from rest_framework.views import APIView
from rest_framework.generics import ListAPIView, RetrieveAPIView, CreateAPIView
from rest_framework.response import Response
from rest_framework import status
from ..models import Orders
from ..serializers import OrdersSerializer, PaymobCallbackSerializer, CreateOrderSerializer, OrdersListSerializer, ReturnOrderRequestSerializer
from orders.services import PaymobServices, OrdersServices
from orders.queryset import ReportQueryset
import constants
from rest_framework.permissions import IsAdminUser
from orders.tasks import update_pending_order


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
                address=serializer.validated_data.get('address'),
            )
            if not order:
                return Response({'error': 'Order not created'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(
                {
                    'error': str(e), 
                    'expired_coupons': e.expired_coupons if hasattr(e, 'expired_coupons') else None,
                }, status= e.status if hasattr(e, 'status') else status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        try:
            payment_url = PaymobServices.create_intention(
                amount=order.discount_price, 
                currency='EGP', 
                biling_data=serializer.data, 
                customer_data=request.user, 
                order=order,
                user=request.user
            )
            # Add to redis the payment link expiry time
            update_pending_order.apply_async(args=(order.id, request.user.id), countdown=constants.PAYMENT_EXPIRY)
        except Exception as e:
            print(e)
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
        serializer = ReturnOrderRequestSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        
        try:
            print(serializer.validated_data['items'][0]['price'])
            OrdersServices.return_order_items(request.user, serializer.validated_data.get('order'), serializer.validated_data.get('items'), serializer.validated_data['reason'])
        except Exception as e:
            return Response({'error': str(e)}, status=e.status if hasattr(e, 'status') else status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(status=status.HTTP_200_OK)

class CancelOrderAPI(APIView):
    def post(self, request):
        if not request.data.get('order_id'):
            return Response({'error': 'Order ID is required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            OrdersServices.cancel_order(request.user, request.data.get('order_id'))
        except Exception as e:
            return Response({'error': str(e)}, status=e.status if hasattr(e, 'status') else status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(status=status.HTTP_200_OK)
    

class ReturnRequestDecisionAPI(APIView):
    permission_classes = [IsAdminUser]
    
    def post(self, request):
        if not request.data.get('request_id') or not request.data.get('status'):
            return Response({'error': 'Return ID and status are required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            OrdersServices.return_request_decision(request.data.get('request_id'), request.data.get('status'))
        except Exception as e:
            return Response({'error': str(e)}, status=e.status if hasattr(e, 'status') else status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(status=status.HTTP_200_OK)
    
    
class PaymentCallbackAPIs(APIView):
    permission_classes = []
    authentication_classes = []
    
    def post(self, request):
        serializer = PaymobCallbackSerializer(data={
            'hmac': request.query_params.get('hmac'),
            'store_order_id': request.data.get('obj').get('payment_key_claims').get('extra').get('store_order_id'),
        }, context={'request': request})
        serializer.is_valid(raise_exception=True)
        
        if request.data.get('obj').get('success'):
            serializer.update(serializer.order, serializer.validated_data)
        else:
            print('failed')
            serializer.order.status = constants.ORDER_FAILED
            serializer.order.save()
            OrdersServices.restore_items(serializer.order, user=serializer.order.user)
        return Response(status=status.HTTP_200_OK)