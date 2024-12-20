from rest_framework.views import APIView
from coupons.serializers import CouponCheckSerializer
from rest_framework.response import Response
from rest_framework import status
from coupons.services import CouponServices
from rest_framework.generics import DestroyAPIView
from cart.models import CartCoupon

class CouponAPIs(APIView):
    def post(self, request):
        serializer = CouponCheckSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        response = CouponServices.apply_coupon(request.user, serializer.coupon)
        return Response(response, status=status.HTTP_200_OK)

    def delete(self, request):
        if not request.data.get('coupon_code'):
            return Response({'error': 'Coupon code is required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            result = CouponServices.remove_cart_coupon(request.user, request.data.get('coupon_code'))
            return Response(result, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({'error': 'Something went wrong'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)