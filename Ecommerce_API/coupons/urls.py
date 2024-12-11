from django.urls import path
from coupons.apis import CouponAPIs

urlpatterns = [
    path('', CouponAPIs.as_view(), name='coupon_apis')
]
