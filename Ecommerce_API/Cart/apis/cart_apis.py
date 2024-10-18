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
                            pv.price,
                            p.id,
                            p.name,
                            JSON_AGG(
                                JSON_BUILD_OBJECT(
                                    'url', pi.url,
                                    'color', pi.color_id
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
        # user_cart_items = Cart.objects.filter(user_id=request.user.id).prefetch_related(
        #     Prefetch(
        #         'product_variant', 
        #         queryset=ProductVariant.objects.only('parent__name', 'parent__seller_id', 'parent__seller__name', 'color', 'price')
        #     )
        # ).annotate(
        #     images=Subquery(
        #         ProductImages.objects.filter(
        #             product_id=OuterRef('product_variant__parent_id'),
        #             color=OuterRef('product_variant__color')
        #         ).annotate(
        #             json_image=Func(
        #                 F('url'),
        #                 F('color'),
        #                 function='json_build_object',
        #                 output_field=JSONField(),
        #             )
        #         ).values('json_image')
        #         .annotate(image_array=ArrayAgg('json_image', distinct=True))
        #         .values('image_array')
        #     )
        # ).all()
        serializer = OutputCartSerializer(user_cart_items, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        if not request.data.get('product_variant'):
            return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)
        if not request.data.get('quantity'):
            return Response({'error': 'Quantity is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            CartServices.add_product_to_cart(request)
        except Exception as e:
            return Response(str(e), status=e.status if hasattr(e, 'status') else status.HTTP_400_BAD_REQUEST)

        
        return Response('cart updated.', status=status.HTTP_201_CREATED)

    def delete(self, request, product_variant):
        cart_product = Cart.objects.filter(user=request.user.id, product_variant=product_variant).first()
        if not cart_product:
            return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)
        cart_product.delete()
        return Response('Product removed from cart', status=status.HTTP_200_OK)