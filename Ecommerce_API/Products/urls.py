from django.urls import path
from .apis import ProductAPIs, ProductList

urlpatterns = [
    path('', ProductList.as_view()),
    path('<int:pk>/', ProductAPIs.as_view()),
]