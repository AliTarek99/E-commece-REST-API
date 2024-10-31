from rest_framework.urls import path
from .apis import OrdersAPIs, PaymentCallbackAPIs, GetOrdersAPIs

urlpatterns = [
    path('create-order/', OrdersAPIs.as_view(), name='orders'),
    path('', GetOrdersAPIs.as_view(), name='get_orders'),
    path('payment/callback/', PaymentCallbackAPIs.as_view(), name='payment_callback')
]