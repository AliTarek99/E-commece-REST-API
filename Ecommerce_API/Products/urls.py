from django.urls import path
from .apis import ProductRetrievalAPIs, ProductDeleteView, ProductCreateView

urlpatterns = [
    path('list/', ProductRetrievalAPIs.as_view()),
    path('<int:id>/', ProductRetrievalAPIs.as_view()),
    path('<int:id>/delete/', ProductDeleteView.as_view()),
    path('', ProductCreateView.as_view()),
]