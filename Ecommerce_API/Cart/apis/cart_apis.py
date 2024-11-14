from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from ..models import Cart
from ..serializers import OutputCartSerializer
from cart.services import CartServices
from products.models import ProductVariant, ProductImages
from django.db.models import Prefetch, OuterRef, Subquery, Func, F, JSONField
from django.contrib.postgres.aggregates import ArrayAgg


class CartAPIs(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get(self, request):
        user_cart_items = Cart.objects.raw("""
                        SELECT
                            c.*,
                            pv.size_id,
                            pv.color_id,
                            pv.price,
                            p.id,
                            p.name,
                            JSON_AGG(
                                JSON_BUILD_OBJECT(
                                    'url', pi.url,
                                    'color_id', pi.color_id,
                                    'default', pi.default
                                )
                            ) AS images
                        FROM
                            cart_cart c
                        JOIN
                            "Product_Variant" pv ON c.product_variant_id = pv.id
                        JOIN
                            "products_product" p ON pv.parent_id = p.id
                        JOIN
                            "Product_Images" pi ON pi.product_id = p.id AND pi.color_id = pv.color_id
                        WHERE
                            c.user_id = %s
                        GROUP BY
                            c.id, p.id, pv.id
                """, [request.user.id])
        processed_items = []
        for item in user_cart_items:
            processed_items.append({
                'product_variant': {
                    'size_id': item.size_id,
                    'color_id': item.color_id,
                    'price': item.price,
                    'id': item.product_variant_id,
                    'parent_id': item.id,
                    'parent': {
                        'name': item.name
                    }
                },
                'quantity': item.quantity,
                'images': item.images,
            })
        # Use the serializer on the processed data
        serializer = OutputCartSerializer(processed_items, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        if not request.data.get('product_variant'):
            return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)
        if not request.data.get('quantity'):
            return Response({'error': 'Quantity is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            cart_item = CartServices.add_product_to_cart(request)
        except Exception as e:
            return Response(str(e), status=e.status if hasattr(e, 'status') else status.HTTP_400_BAD_REQUEST)

        
        return Response({'quantity': cart_item.validated_data['quantity']}, status=status.HTTP_201_CREATED)

    def delete(self, request, product_variant):
        cart_product = Cart.objects.filter(user=request.user.id, product_variant=product_variant).first()
        if not cart_product:
            return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)
        cart_product.delete()
        return Response('Product removed from cart', status=status.HTTP_200_OK)