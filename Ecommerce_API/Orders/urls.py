from rest_framework.urls import path
from .apis import OrdersAPIs, PaymentCallbackAPIs, GetOrdersListAPIs, ReorderAPI, SalesReportAPI, GetOrderDetailsAPIs, CancelOrderAPI, ReturnOrderAPI, ReturnRequestDecisionAPI

urlpatterns = [
    path('create-order/', OrdersAPIs.as_view(), name='orders'),
    path('', GetOrdersListAPIs.as_view(), name='get_orders'),
    path('reorder/', ReorderAPI.as_view(), name='reorder'),
    path('payment/callback/', PaymentCallbackAPIs.as_view(), name='payment_callback'),
    path('sales-report/', SalesReportAPI.as_view(), name='sales_report'),
    path('<int:id>/', GetOrderDetailsAPIs.as_view(), name='get_order_details'),
    path('return/', ReturnOrderAPI.as_view(), name='return_order'),
    path('cancel/', CancelOrderAPI.as_view(), name='cancel_order'),
    path('return-request-decision/', ReturnRequestDecisionAPI.as_view(), name='return_decision'),
]