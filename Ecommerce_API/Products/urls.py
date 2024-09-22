from django.urls import path
from .apis import ProductAPIs, ProductList

urlpatterns = [
    path('list/', ProductList.as_view()),
    path('<int:pk>/', ProductAPIs.as_view()),
    path('', ProductAPIs.as_view()),
]