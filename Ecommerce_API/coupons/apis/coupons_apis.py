from rest_framework.views import APIView
from coupons.serializers import CouponCheckSerializer
from rest_framework.response import Response
from rest_framework import status
from coupons.services import CouponServices

class CouponAPIs(APIView):
    def post(self, request):
        serializer = CouponCheckSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        response = CouponServices.apply_coupon(request.user, serializer.coupon)
        return Response(response, status=status.HTTP_200_OK)